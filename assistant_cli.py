#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys
import textwrap
from pathlib import Path
from typing import List, Dict, Any

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

ROOT = Path(__file__).resolve().parent
INDEX_PATH = ROOT / ".assistant_index.json"

FILE_EXTENSIONS = {".md", ".txt", ".csv", ".json", ".yaml", ".yml"}
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache"}


def iter_repo_files(root: Path):
    for path in root.rglob("*"):
        if path.is_file() and not any(part in SKIP_DIRS for part in path.parts):
            if path.suffix.lower() in FILE_EXTENSIONS or path.name.lower().endswith(".md"):
                yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""


def chunk_text(text: str, max_chars: int = 900) -> List[str]:
    cleaned = re.sub(r"\r\n?", "\n", text)
    cleaned = cleaned.strip()
    if not cleaned:
        return []

    paragraphs = re.split(r"\n\s*\n+", cleaned)
    chunks: List[str] = []
    current = ""

    for para in paragraphs:
        para = " ".join(para.split())
        if not para:
            continue
        if len(current) + len(para) + 1 <= max_chars:
            current = (current + " " + para).strip()
        else:
            if current:
                chunks.append(current)
            if len(para) > max_chars:
                for i in range(0, len(para), max_chars):
                    piece = para[i : i + max_chars].strip()
                    if piece:
                        chunks.append(piece)
                current = ""
            else:
                current = para

    if current:
        chunks.append(current)

    return [c for c in chunks if len(c.strip()) > 60]


def build_index(root: Path) -> Dict[str, Any]:
    chunks = []
    for path in sorted(iter_repo_files(root)):
        rel = path.relative_to(root).as_posix()
        text = read_text(path)
        for chunk in chunk_text(text):
            chunks.append({
                "path": rel,
                "text": chunk,
                "source": rel,
            })

    payload = {"generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z", "chunks": chunks}
    INDEX_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def load_index(force_refresh: bool = False) -> Dict[str, Any]:
    if force_refresh or not INDEX_PATH.exists():
        return build_index(ROOT)
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return build_index(ROOT)


def normalize_query(question: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z0-9_]+", question.lower())
    cleaned = [t for t in tokens if len(t) > 2]
    return cleaned


def rank_chunks(question: str, chunks: List[Dict[str, Any]], limit: int = 6) -> List[Dict[str, Any]]:
    tokens = normalize_query(question)
    if not tokens:
        return chunks[:limit]

    scored = []
    for chunk in chunks:
        text = (chunk.get("path", "") + " " + chunk.get("text", "")).lower()
        token_count = sum(1 for token in tokens if token in text)
        path_score = sum(3 for token in tokens if token in chunk.get("path", "").lower())
        score = token_count * 2 + path_score
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    ranked = [chunk for _, chunk in scored[:limit]]
    if not ranked:
        ranked = chunks[:limit]
    return ranked


def build_context(question: str, chunks: List[Dict[str, Any]], limit: int = 5) -> str:
    ranked = rank_chunks(question, chunks, limit=limit)
    if not ranked:
        return "No relevant repo context was found."

    parts = []
    for item in ranked:
        snippet = item["text"].strip()
        if len(snippet) > 1200:
            snippet = snippet[:1200].rstrip() + "..."
        parts.append(f"[{item['path']}]:\n{snippet}\n")
    return "\n\n".join(parts)


def offline_answer(question: str, chunks: List[Dict[str, Any]]) -> str:
    context = build_context(question, chunks, limit=5)
    if context.startswith("No relevant repo"):
        return context

    answer = (
        "I checked the repo contents and the strongest matches are: \n\n"
        f"{context}\n\n"
        "This is based on the files currently in the repo, not on live external data."
    )
    return answer


def try_ollama(question: str, context: str) -> str:
    if not requests:
        return ""

    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    url = host.rstrip("/") + "/api/generate"
    payload = {
        "model": model,
        "prompt": (
            "Answer only from the supplied context. Be concise and grounded in the text.\n\n"
            f"Context:\n{context}\n\nQuestion:\n{question}\n\nAnswer:"
        ),
        "stream": False,
    }

    try:
        r = requests.post(url, json=payload, timeout=25)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and "response" in data:
                return data["response"].strip()
    except Exception:
        pass
    return ""


def try_openai(question: str, context: str) -> str:
    if not requests:
        return ""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return ""

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": "You are a grounded terminal assistant. Answer only from the supplied context and be concise.",
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion:\n{question}",
            },
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        r = requests.post("https://api.openai.com/v1/responses", headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            data = r.json()
            output = data.get("output") or []
            texts = []
            for item in output:
                if isinstance(item, dict):
                    content = item.get("content") or []
                    for c in content:
                        if isinstance(c, dict) and isinstance(c.get("text"), str):
                            texts.append(c["text"])
            if texts:
                return "\n".join(texts).strip()
    except Exception:
        pass
    return ""


def answer_question(question: str, force_refresh: bool = False) -> str:
    state = load_index(force_refresh)
    chunks = state.get("chunks", [])
    context = build_context(question, chunks, limit=5)

    if os.getenv("OLLAMA_MODEL") or os.getenv("OLLAMA_HOST"):
        llm_answer = try_ollama(question, context)
        if llm_answer:
            return llm_answer

    if os.getenv("OPENAI_API_KEY"):
        llm_answer = try_openai(question, context)
        if llm_answer:
            return llm_answer

    return offline_answer(question, chunks)


def interactive_chat() -> None:
    print("Local AI assistant ready. Type 'exit' or 'quit' to stop.")
    while True:
        try:
            user_input = input("assistant> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "q"}:
            print("Goodbye.")
            break

        print(answer_question(user_input))


def main() -> int:
    parser = argparse.ArgumentParser(description="Local AI assistant for repo-grounded questions.")
    subparsers = parser.add_subparsers(dest="command")

    ask_parser = subparsers.add_parser("ask", help="Ask a single question")
    ask_parser.add_argument("question", nargs="+", help="Question to ask")

    chat_parser = subparsers.add_parser("chat", help="Start an interactive terminal chat")
    chat_parser.add_argument("--refresh", action="store_true", help="Refresh the local index before answering")

    index_parser = subparsers.add_parser("index", help="Rebuild the repo index")

    args = parser.parse_args()

    if args.command == "ask":
        question = " ".join(args.question)
        print(answer_question(question))
        return 0

    if args.command == "chat":
        interactive_chat()
        return 0

    if args.command == "index":
        build_index(ROOT)
        print(f"Rebuilt repo index at {INDEX_PATH}")
        return 0

    print("No command supplied. Use 'ask', 'chat', or 'index'.")
    return 1


if __name__ == "__main__":
    sys.exit(main())


#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

ROOT = Path(__file__).resolve().parent
INDEX_PATH = ROOT / ".assistant_index.json"
MEMORY_PATH = ROOT / ".assistant_memory.json"

FILE_EXTENSIONS = {".md", ".txt", ".csv", ".json", ".yaml", ".yml", ".py", ".js", ".ts", ".sh"}
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache", ".idea", ".DS_Store"}


def normalize_path(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    if raw.startswith("./"):
        raw = raw[2:]
    return raw.replace("\\", "/")


def resolve_repo_path(raw: str) -> Path:
    rel = normalize_path(raw)
    if not rel or rel in {".", "/"}:
        return ROOT
    return (ROOT / rel).resolve()


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
    cleaned = re.sub(r"\r\n?", "\n", text).strip()
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
            chunks.append({"path": rel, "text": chunk, "source": rel})

    payload = {"generated_at": datetime.utcnow().isoformat() + "Z", "chunks": chunks}
    INDEX_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def load_index(force_refresh: bool = False) -> Dict[str, Any]:
    if force_refresh or not INDEX_PATH.exists():
        return build_index(ROOT)
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return build_index(ROOT)


def load_memory() -> Dict[str, Any]:
    if MEMORY_PATH.exists():
        try:
            return json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {"history": []}
    return {"history": []}


def save_memory(data: Dict[str, Any]) -> None:
    MEMORY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def remember_last_question(question: str) -> None:
    data = load_memory()
    history = data.setdefault("history", [])
    history.append({"question": question, "timestamp": datetime.utcnow().isoformat() + "Z"})
    data["last_question"] = question
    save_memory(data)


def show_memory() -> str:
    data = load_memory()
    history = data.get("history", [])
    if not history:
        return "No chat history yet."
    lines = ["Recent history:"]
    for item in history[-8:]:
        lines.append(f"- {item.get('timestamp')} :: {item.get('question')}")
    return "\n".join(lines)


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
        token_hits = sum(1 for token in tokens if token in text)
        path_hits = sum(3 for token in tokens if token in chunk.get("path", "").lower())
        score = token_hits * 2 + path_hits
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

    return (
        "I checked the repo and the best matches are:\n\n"
        f"{context}\n\n"
        "This answer is grounded only in the files currently in the repo."
    )


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


def summarize_file(path: str) -> str:
    target = resolve_repo_path(path)
    if not target.exists():
        return f"File not found: {path}"
    if target.is_dir():
        return summarize_directory(path)

    text = read_text(target)
    if not text:
        return f"No readable text in: {path}"

    lines = text.splitlines()
    preview = "\n".join(lines[:60])
    return f"Summary for {path}\n\n{preview[:2200]}"


def summarize_directory(path: str) -> str:
    target = resolve_repo_path(path)
    if not target.exists() or not target.is_dir():
        return f"Directory not found: {path}"

    files = []
    for p in sorted(target.rglob("*")):
        if p.is_file() and not any(part in SKIP_DIRS for part in p.parts):
            if p.suffix.lower() in FILE_EXTENSIONS or p.name.lower().endswith(".md"):
                files.append(p.relative_to(ROOT).as_posix())

    if not files:
        return f"No readable files found in: {path}"

    result = [f"Directory summary for {path}", ""]
    for f in files[:60]:
        result.append(f"- {f}")
    if len(files) > 60:
        result.append(f"... and {len(files) - 60} more files")
    return "\n".join(result)


def search_repo(term: str) -> str:
    state = load_index(False)
    chunks = state.get("chunks", [])
    q = term.strip()
    if not q:
        return "Please provide a search term."

    matches = []
    for chunk in chunks:
        text = (chunk.get("path", "") + " " + chunk.get("text", "")).lower()
        if q.lower() in text:
            matches.append(chunk)

    if not matches:
        return f"No matches for: {term}"

    output = [f"Search results for '{term}':"]
    for item in matches[:12]:
        output.append(f"- {item['path']}")
        snippet = item["text"]
        if len(snippet) > 220:
            snippet = snippet[:220].rstrip() + "..."
        output.append(f"  {snippet}")
    return "\n".join(output)


def compare_files(file_a: str, file_b: str) -> str:
    def load_terms(path: str) -> Dict[str, int]:
        p = resolve_repo_path(path)
        text = read_text(p)
        words = re.findall(r"[a-zA-Z0-9_]+", text.lower())
        counts: Dict[str, int] = {}
        for w in words:
            if len(w) < 4:
                continue
            counts[w] = counts.get(w, 0) + 1
        return counts

    a_counts = load_terms(file_a)
    b_counts = load_terms(file_b)

    common = sorted(set(a_counts).intersection(b_counts), key=lambda w: (a_counts[w] + b_counts[w]), reverse=True)[:10]
    unique_a = sorted(set(a_counts) - set(b_counts), key=lambda w: a_counts[w], reverse=True)[:10]
    unique_b = sorted(set(b_counts) - set(a_counts), key=lambda w: b_counts[w], reverse=True)[:10]

    summary = [f"Comparison: {file_a} vs {file_b}"]
    summary.append(f"Common significant terms: {', '.join(common) if common else 'none'}")
    summary.append(f"Terms more prominent in {file_a}: {', '.join(unique_a) if unique_a else 'none'}")
    summary.append(f"Terms more prominent in {file_b}: {', '.join(unique_b) if unique_b else 'none'}")
    return "\n".join(summary)


def interactive_chat() -> None:
    print("Local AI assistant ready. Commands: help, ask, search, summary, compare, list, memory, exit")
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

        if user_input.lower() == "help":
            print("Commands:\n- ask <question>\n- search <term>\n- summary <path>\n- compare <file_a> <file_b>\n- list <directory>\n- memory\n- exit")
            continue

        if user_input.lower() == "memory":
            print(show_memory())
            continue

        parts = user_input.split()
        cmd = parts[0].lower()

        if cmd == "ask":
            question = " ".join(parts[1:])
            if not question:
                print("Please provide a question.")
                continue
            remember_last_question(question)
            print(answer_question(question))
            continue

        if cmd == "list":
            target = parts[1] if len(parts) > 1 else "."
            print(summarize_directory(target))
            continue

        if cmd == "search":
            term = " ".join(parts[1:])
            if not term:
                print("Please provide a search term.")
                continue
            print(search_repo(term))
            continue

        if cmd == "summary":
            target = parts[1] if len(parts) > 1 else "."
            if target == ".":
                print(summarize_directory(target))
            else:
                target_path = resolve_repo_path(target)
                if target_path.is_dir():
                    print(summarize_directory(target))
                else:
                    print(summarize_file(target))
            continue

        if cmd == "compare":
            if len(parts) < 3:
                print("Usage: compare <file_a> <file_b>")
                continue
            print(compare_files(parts[1], parts[2]))
            continue

        print(answer_question(user_input))


def main() -> int:
    parser = argparse.ArgumentParser(description="Local AI assistant for repo-grounded questions, search, and summaries.")
    subparsers = parser.add_subparsers(dest="command")

    ask_parser = subparsers.add_parser("ask", help="Ask a repo-grounded question")
    ask_parser.add_argument("question", nargs="+", help="Question to ask")

    chat_parser = subparsers.add_parser("chat", help="Start interactive chat")

    index_parser = subparsers.add_parser("index", help="Rebuild the repo index")

    search_parser = subparsers.add_parser("search", help="Search the repo")
    search_parser.add_argument("term", nargs="+", help="Search term")

    summary_parser = subparsers.add_parser("summary", help="Summarize a file or directory")
    summary_parser.add_argument("path", nargs="?", default=".", help="File or directory path")

    compare_parser = subparsers.add_parser("compare", help="Compare two files")
    compare_parser.add_argument("file_a", help="First file")
    compare_parser.add_argument("file_b", help="Second file")

    list_parser = subparsers.add_parser("list", help="List files in a directory")
    list_parser.add_argument("path", nargs="?", default=".", help="Directory path")

    memory_parser = subparsers.add_parser("memory", help="Show recent chat history")

    args = parser.parse_args()

    if args.command == "ask":
        question = " ".join(args.question)
        remember_last_question(question)
        print(answer_question(question))
        return 0

    if args.command == "chat":
        interactive_chat()
        return 0

    if args.command == "index":
        build_index(ROOT)
        print(f"Rebuilt repo index at {INDEX_PATH}")
        return 0

    if args.command == "search":
        print(search_repo(" ".join(args.term)))
        return 0

    if args.command == "summary":
        target = args.path or "."
        if target == ".":
            print(summarize_directory(target))
        else:
            target_path = resolve_repo_path(target)
            if target_path.is_dir():
                print(summarize_directory(target))
            else:
                print(summarize_file(target))
        return 0

    if args.command == "compare":
        print(compare_files(args.file_a, args.file_b))
        return 0

    if args.command == "list":
        print(summarize_directory(args.path or "."))
        return 0

    if args.command == "memory":
        print(show_memory())
        return 0

    print("No command supplied. Use 'ask', 'chat', 'index', 'search', 'summary', 'compare', or 'list'.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

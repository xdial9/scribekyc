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
SESSION_PATH = ROOT / ".assistant_sessions.json"

FILE_EXTENSIONS = {".md", ".txt", ".csv", ".json", ".yaml", ".yml", ".py", ".js", ".ts", ".sh"}
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache", ".idea", "__MACOSX"}

SYNONYM_MAP = {
    "idv": ["idv", "identity verification", "identity-verification", "kyc"],
    "kyc": ["kyc", "identity verification", "identity-verification", "customer onboarding"],
    "liveness": ["liveness", "facial liveness", "anti spoof", "spoofing", "face verification"],
    "document": ["document", "passport", "driver license", "id document", "id card"],
    "vendor": ["vendor", "provider", "company", "platform"],
    "risk": ["risk", "threat", "fraud", "attack", "vulnerability"],
    "compare": ["compare", "difference", "contrast"],
    "summary": ["summary", "overview", "what is this"],
}


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


def append_memory(question: str, answer: str) -> None:
    data = load_memory()
    history = data.setdefault("history", [])
    history.append({
        "question": question,
        "answer": answer[:2000],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })
    if len(history) > 30:
        history = history[-30:]
    data["history"] = history
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


def load_sessions() -> Dict[str, List[Dict[str, str]]]:
    if SESSION_PATH.exists():
        try:
            return json.loads(SESSION_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_sessions(data: Dict[str, List[Dict[str, str]]]) -> None:
    SESSION_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def session_names() -> List[str]:
    return sorted(load_sessions().keys())


def get_session_context(session_id: str, max_turns: int = 5) -> str:
    histories = load_sessions().get(session_id, [])
    if not histories:
        return ""

    recent = histories[-max_turns:]
    turns = []
    for item in recent:
        q = item.get("question", "").strip()
        a = item.get("answer", "").strip()
        if q:
            turns.append(f"Q: {q}\nA: {a}")
    if not turns:
        return ""
    return "Prior chat context:\n" + "\n\n".join(turns)


def append_session_turn(session_id: str, question: str, answer: str) -> None:
    sessions = load_sessions()
    history = sessions.setdefault(session_id, [])
    history.append({
        "question": question,
        "answer": answer[:2000],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })
    if len(history) > 30:
        history = history[-30:]
    sessions[session_id] = history
    save_sessions(sessions)


def expand_query_tokens(question: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z0-9_\-]+", question.lower())
    expanded = []
    for token in tokens:
        expanded.append(token)
        for key, variants in SYNONYM_MAP.items():
            if token in key or key in token:
                expanded.extend(variants)
            elif token in variants:
                expanded.append(key)
    return [t for t in expanded if len(t) > 2]


def score_chunk(question: str, chunk: Dict[str, Any]) -> float:
    q = question.lower()
    text = (chunk.get("path", "") + " " + chunk.get("text", "")).lower()
    tokens = expand_query_tokens(q)
    if not tokens:
        return 0.0

    exact_phrase = 1.0 if q in text else 0.0
    path_matches = sum(3 for token in tokens if token in chunk.get("path", "").lower())
    text_matches = sum(2 for token in tokens if token in text)
    unique_hits = sum(1 for token in set(tokens) if token in text)
    score = exact_phrase * 20 + path_matches + text_matches + unique_hits * 1.5

    if any(token in text for token in ["vendor", "liveness", "kyc", "document", "risk"]):
        score += 1.0

    return score


def rank_chunks(question: str, chunks: List[Dict[str, Any]], limit: int = 6) -> List[Dict[str, Any]]:
    scored = [(score_chunk(question, chunk), chunk) for chunk in chunks]
    scored = [item for item in scored if item[0] > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
    ranked = [chunk for _, chunk in scored[:limit]]
    if not ranked:
        return chunks[:limit]
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


def build_repo_overview() -> str:
    files = []
    for path in sorted(iter_repo_files(ROOT)):
        rel = path.relative_to(ROOT).as_posix()
        files.append(rel)

    summary_lines = [
        "Project overview:",
        "- This repo contains a local AI assistant, a research corpus, and review templates.",
        "- The main implementation is in assistant_cli.py and app.py.",
        "- The vendor research sits under research/ and docs/.",
        "",
        "Key files:",
    ]

    for f in files[:80]:
        summary_lines.append(f"- {f}")

    if len(files) > 80:
        summary_lines.append(f"... and {len(files) - 80} more files")

    summary_lines.extend([
        "",
        "Interpretation:",
        "- This repo is organized as a local knowledge base for project notes, vendor research, and structured analysis.",
        "- The assistant is designed to answer grounded questions from local files instead of external internet data.",
        "- The web app is a simple interface for the same repository-aware workflow.",
    ])
    return "\n".join(summary_lines)


def offline_answer(question: str, chunks: List[Dict[str, Any]], session_context: str = "") -> str:
    context = build_context(question, chunks, limit=5)
    if context.startswith("No relevant repo"):
        return context

    if session_context:
        context = context + "\n\n" + session_context

    return (
        "I checked the repo and the best matches are:\n\n"
        f"{context}\n\n"
        "This answer is grounded only in the files currently in the repo."
    )


def try_ollama(question: str, context: str) -> str:
    if not requests:
        return ""

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
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


def answer_question(question: str, session_id: str = "default", force_refresh: bool = False) -> str:
    normalized = question.strip()
    if not normalized:
        return "Please enter a question."

    if normalized.lower() in {"overview", "repo overview", "what is this repo", "what is this project"}:
        return build_repo_overview()

    state = load_index(force_refresh)
    chunks = state.get("chunks", [])
    context = build_context(normalized, chunks, limit=6)

    session_context = get_session_context(session_id, max_turns=5)
    if session_context:
        context = context + "\n\n" + session_context

    if os.getenv("OLLAMA_MODEL") or os.getenv("OLLAMA_HOST"):
        llm_answer = try_ollama(normalized, context)
        if llm_answer:
            return llm_answer

    if os.getenv("OPENAI_API_KEY"):
        llm_answer = try_openai(normalized, context)
        if llm_answer:
            return llm_answer

    return offline_answer(normalized, chunks, session_context=session_context)


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


def get_folder_tree(base: str = ".", max_depth: int = 2) -> List[Dict[str, Any]]:
    root = resolve_repo_path(base)
    if not root.exists() or not root.is_dir():
        return []

    def walk(directory: Path, depth: int = 0):
        if depth > max_depth:
            return []
        items = []
        for child in sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            if child.name in SKIP_DIRS:
                continue
            if child.is_dir():
                items.append({
                    "name": child.name,
                    "path": child.relative_to(ROOT).as_posix(),
                    "type": "dir",
                    "children": walk(child, depth + 1),
                })
            else:
                if child.suffix.lower() in FILE_EXTENSIONS or child.name.lower().endswith(".md"):
                    items.append({
                        "name": child.name,
                        "path": child.relative_to(ROOT).as_posix(),
                        "type": "file",
                    })
        return items

    return walk(root, 0)


def interactive_chat() -> None:
    print("Local AI assistant ready. Commands: help, ask, search, summary, compare, list, overview, memory, exit")
    session = "default"
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
            print("Commands:\n- ask <question>\n- search <term>\n- summary <path>\n- compare <file_a> <file_b>\n- list <directory>\n- overview\n- memory\n- session <name>\n- exit")
            continue

        if user_input.lower() == "overview":
            print(build_repo_overview())
            continue

        if user_input.lower() == "memory":
            print(show_memory())
            continue

        if user_input.lower().startswith("session "):
            session = user_input.split(maxsplit=1)[1].strip() or "default"
            print(f"Session set to: {session}")
            continue

        parts = user_input.split()
        cmd = parts[0].lower()

        if cmd == "ask":
            question = " ".join(parts[1:])
            if not question:
                print("Please provide a question.")
                continue
            answer = answer_question(question, session_id=session)
            append_memory(question, answer)
            append_session_turn(session, question, answer)
            print(answer)
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

        answer = answer_question(user_input, session_id=session)
        append_memory(user_input, answer)
        append_session_turn(session, user_input, answer)
        print(answer)


def main() -> int:
    parser = argparse.ArgumentParser(description="Local AI assistant for repo-grounded questions, search, summaries, overview, and session memory.")
    subparsers = parser.add_subparsers(dest="command")

    ask_parser = subparsers.add_parser("ask", help="Ask a repo-grounded question")
    ask_parser.add_argument("question", nargs="+", help="Question to ask")
    ask_parser.add_argument("--session", default="default", help="Session name to keep chat memory")

    chat_parser = subparsers.add_parser("chat", help="Start interactive chat")
    chat_parser.add_argument("--session", default="default", help="Default session name")

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

    overview_parser = subparsers.add_parser("overview", help="Show repo overview")

    sessions_parser = subparsers.add_parser("sessions", help="List chat sessions")

    args = parser.parse_args()

    if args.command == "ask":
        question = " ".join(args.question)
        answer = answer_question(question, session_id=args.session)
        append_memory(question, answer)
        append_session_turn(args.session, question, answer)
        print(answer)
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

    if args.command == "overview":
        print(build_repo_overview())
        return 0

    if args.command == "sessions":
        sessions = session_names()
        print("\n".join(f"- {s}" for s in sessions) if sessions else "No sessions yet.")
        return 0

    print("No command supplied. Use 'ask', 'chat', 'index', 'search', 'summary', 'compare', 'list', 'memory', 'sessions', or 'overview'.")
    return 1


if __name__ == "__main__":
    sys.exit(main())


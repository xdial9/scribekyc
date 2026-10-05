#!/usr/bin/env python3
"""
Scribe web UI — standard library only, no extra dependencies.

Usage:
    python3 scribe_web.py [--repo PATH] [--port 5000]

Then open http://localhost:5000 in a browser.
"""

import argparse
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

import app as scribe


def esc(text: str) -> str:
    return html.escape(text or "")


def render_tree(nodes, depth=0) -> str:
    parts = ["<ul>"]
    for node in nodes:
        if node["type"] == "dir":
            parts.append(
                f"<li>📁 {esc(node['name'])}"
                + render_tree(node.get("children", []), depth + 1)
                + "</li>"
            )
        else:
            parts.append(
                f"<li>📄 <a href=\"/view?p={esc(node['path'])}\">{esc(node['name'])}</a></li>"
            )
    parts.append("</ul>")
    return "".join(parts)


def layout(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Scribe — {esc(title)}</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }}
nav a {{ margin-right: 1rem; }}
pre {{ background: #f4f4f4; padding: 1rem; overflow-x: auto; white-space: pre-wrap; }}
ul {{ list-style: none; padding-left: 1.2rem; }}
input[type=text] {{ width: 70%; padding: 0.4rem; }}
button {{ padding: 0.4rem 0.8rem; }}
.result {{ border-bottom: 1px solid #ddd; padding: 0.6rem 0; }}
</style></head>
<body>
<nav><a href="/">🏠 Home</a> <a href="/askform">💬 Ask</a> <a href="/searchform">🔍 Search</a></nav>
<h1>Scribe</h1>
<p><small>Target folder: {esc(str(scribe.ROOT))}</small></p>
{body}
</body></html>"""


def render_home() -> str:
    tree = scribe.get_folder_tree(".", max_depth=3)
    return "<h2>Files</h2>" + (render_tree(tree) if tree else "<p>No readable files found.</p>")


def render_view(path: str) -> str:
    target = scribe.resolve_repo_path(path)
    if target is None or not target.is_file():
        return f"<p>File not found: {esc(path)}</p>"
    text = scribe.read_text(target)
    return f"<h2>{esc(path)}</h2><pre>{esc(text[:20000])}</pre>"


def render_search_form() -> str:
    return """<h2>Search</h2>
<form action="/search" method="get">
<input type="text" name="q" placeholder="search term" autofocus>
<button type="submit">Search</button></form>"""


def render_search(q: str) -> str:
    if not q.strip():
        return "<p>Enter a search term.</p>"
    out = scribe.search_repo(q)
    blocks = []
    for line in out.splitlines():
        if line.startswith("- "):
            blocks.append(f"<div class='result'><strong>{esc(line[2:])}</strong>")
        elif line.startswith("  "):
            blocks.append(f"<br><small>{esc(line.strip())}</small></div>")
        else:
            blocks.append(f"<p>{esc(line)}</p>")
    return f"<h2>Search: {esc(q)}</h2>" + "".join(blocks)


def render_ask_form() -> str:
    return """<h2>Ask</h2>
<form action="/ask" method="get">
<input type="text" name="q" placeholder="ask a question about the repo" autofocus>
<button type="submit">Ask</button></form>"""


def render_ask(q: str) -> str:
    if not q.strip():
        return "<p>Enter a question.</p>"
    answer = scribe.answer_question(q)
    return f"<h2>Q: {esc(q)}</h2><pre>{esc(answer)}</pre>"


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: str) -> None:
        data = layout("web", body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        path = parsed.path
        if path == "/view":
            self._send(render_view(qs.get("p", [""])[0]))
        elif path == "/search":
            self._send(render_search(qs.get("q", [""])[0]))
        elif path == "/searchform":
            self._send(render_search_form())
        elif path == "/ask":
            self._send(render_ask(qs.get("q", [""])[0]))
        elif path == "/askform":
            self._send(render_ask_form())
        else:
            self._send(render_home())

    def log_message(self, *args) -> None:  # keep the terminal quiet
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Scribe web UI (stdlib only).")
    parser.add_argument("--repo", "-r", default=".", help="Folder to browse/search")
    parser.add_argument("--port", "-p", type=int, default=5000, help="Port to serve on")
    args = parser.parse_args()

    root = scribe.set_repo_root(args.repo)
    if not root.is_dir():
        print(f"Repo not found: {args.repo}")
        raise SystemExit(2)

    server = HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Scribe web UI serving {root} at http://localhost:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()

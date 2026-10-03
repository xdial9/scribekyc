#!/usr/bin/env python3

from flask import Flask, render_template_string, request

from assistant_cli import (
    answer_question,
    build_repo_overview,
    get_folder_tree,
    session_names,
    append_session_turn,
    show_memory,
    read_text,
    resolve_repo_path,
)

app = Flask(__name__)

HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Local Repo Assistant</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        max-width: 1200px;
        margin: 40px auto;
        padding: 0 20px;
        background: #0b1220;
        color: #e5e7eb;
      }
      .panel {
        background: #111827;
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 18px;
      }
      textarea, input, button, select {
        width: 100%;
        box-sizing: border-box;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #475569;
        background: #020817;
        color: #f8fafc;
        margin-top: 8px;
      }
      button {
        background: #2563eb;
        cursor: pointer;
        font-weight: bold;
      }
      pre {
        white-space: pre-wrap;
        background: #020817;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 14px;
        overflow: auto;
      }
      .layout {
        display: grid;
        grid-template-columns: 320px 1.5fr;
        gap: 18px;
      }
      .tree {
        list-style: none;
        padding-left: 0;
        margin: 0;
      }
      .tree li {
        margin: 6px 0;
      }
      .tree a {
        color: #cbd5e1;
        text-decoration: none;
      }
      @media (max-width: 800px) {
        .layout { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <div class="panel">
      <h1>Local Repo Assistant</h1>
      <form method="post" action="/ask">
        <div style="display:flex; gap:12px; align-items:center;">
          <div style="flex:1;">
            <label for="session">Session</label>
            <select name="session" id="session">
              {% for s in sessions %}
                <option value="{{ s }}" {% if s == active_session %}selected{% endif %}>{{ s }}</option>
              {% endfor %}
            </select>
          </div>
          <div style="flex:1;">
            <label for="folder">Folder</label>
            <input name="folder" value="{{ active_folder }}" placeholder="." />
          </div>
        </div>
        <label for="question">Question</label>
        <textarea name="question" rows="4" placeholder="Ask about the repo, vendor research, docs, or compare files..."></textarea>
        <button type="submit">Ask</button>
      </form>
    </div>

    <div class="layout">
      <aside class="panel">
        <h2>Folder tree</h2>
        <ul class="tree">
          {% for item in folder_tree %}
            <li>
              {% if item.type == 'dir' %}
                <strong>{{ item.name }}/</strong>
                {% if item.children %}
                  <ul class="tree">
                    {% for child in item.children %}
                      <li>
                        {% if child.type == 'dir' %}
                          <strong>{{ child.name }}/</strong>
                        {% else %}
                          <a href="/file/{{ child.path }}">{{ child.name }}</a>
                        {% endif %}
                      </li>
                    {% endfor %}
                  </ul>
                {% endif %}
              {% else %}
                <a href="/file/{{ item.path }}">{{ item.name }}</a>
              {% endif %}
            </li>
          {% endfor %}
        </ul>
      </aside>

      <div>
        <div class="panel">
          <h2>Answer</h2>
          <pre>{{ answer }}</pre>
        </div>

        <div class="panel">
          <h2>Overview</h2>
          <pre>{{ overview }}</pre>
        </div>

        <div class="panel">
          <h2>Session memory</h2>
          <pre>{{ memory }}</pre>
        </div>
      </div>
    </div>
  </body>
</html>
"""


def render_page(answer: str = "Ask a question to see the repo-grounded answer.", active_session: str = "default", active_folder: str = "."):
    sessions = session_names() or ["default"]
    if active_session not in sessions:
        sessions = [active_session] + sessions
    tree = get_folder_tree(active_folder)
    return render_template_string(
        HTML,
        answer=answer,
        overview=build_repo_overview(),
        memory=show_memory(),
        sessions=sessions,
        active_session=active_session,
        active_folder=active_folder,
        folder_tree=tree,
    )


@app.get("/")
def index():
    return render_page()


@app.get("/file/<path:file_path>")
def file_view(file_path: str):
    path = resolve_repo_path(file_path)
    if path.exists() and path.is_file():
        content = read_text(path)
        answer = f"Selected file: {file_path}\n\n" + (content[:5000] if content else "(empty file)")
    else:
        answer = f"Selected file: {file_path}\n\nFile not found or not readable."
    return render_page(answer=answer, active_folder=".")


@app.post("/ask")
def ask():
    question = request.form.get("question", "").strip()
    session = request.form.get("session", "default").strip() or "default"
    folder = request.form.get("folder", ".").strip() or "."

    if not question:
        answer = "Please enter a question."
    else:
        answer = answer_question(question, session_id=session)
        append_session_turn(session, question, answer)

    return render_page(answer=answer, active_session=session, active_folder=folder)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


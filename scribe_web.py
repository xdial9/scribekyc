#!/usr/bin/env python3

from flask import Flask, render_template_string, request

from scribe_cli import (
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
    <title>Scribe — Local Repo Assistant</title>
    <style>
      body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        max-width: 1200px;
        margin: 40px auto;
        padding: 0 20px;
        background: linear-gradient(135deg, #0b1220 0%, #1a2a4e 100%);
        color: #e5e7eb;
      }
      .header {
        text-align: center;
        margin-bottom: 32px;
      }
      .header h1 {
        font-size: 2.5em;
        margin: 0;
        background: linear-gradient(135deg, #60a5fa, #93c5fd);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 2px;
      }
      .header p {
        margin-top: 8px;
        color: #a0aec0;
        font-size: 0.9em;
      }
      .panel {
        background: #111827;
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 18px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
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
        font-family: 'Segoe UI', monospace;
      }
      button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        cursor: pointer;
        font-weight: bold;
        transition: all 0.3s ease;
      }
      button:hover {
        background: linear-gradient(135deg, #1d4ed8, #1e40af);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
      }
      pre {
        white-space: pre-wrap;
        background: #020817;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 14px;
        overflow: auto;
        font-size: 0.85em;
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
        color: #60a5fa;
        text-decoration: none;
        transition: color 0.2s ease;
      }
      .tree a:hover {
        color: #93c5fd;
      }
      .tree strong {
        color: #e5e7eb;
      }
      .form-row {
        display: flex;
        gap: 12px;
        align-items: flex-start;
      }
      .form-row > div {
        flex: 1;
      }
      .form-row label {
        display: block;
        font-weight: bold;
        margin-bottom: 4px;
        font-size: 0.85em;
      }
      .badge {
        display: inline-block;
        background: #2563eb;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.75em;
        font-weight: bold;
        margin-right: 4px;
      }
      @media (max-width: 800px) {
        .layout { grid-template-columns: 1fr; }
        .form-row { flex-direction: column; }
        .header h1 { font-size: 1.8em; }
      }
    </style>
  </head>
  <body>
    <div class="header">
      <h1>✍️ SCRIBE</h1>
      <p>Local repo-grounded assistant for project exploration and synthesis</p>
    </div>

    <div class="panel">
      <form method="post" action="/ask">
        <div class="form-row">
          <div>
            <label for="session">Session</label>
            <select name="session" id="session">
              {% for s in sessions %}
                <option value="{{ s }}" {% if s == active_session %}selected{% endif %}>{{ s }}</option>
              {% endfor %}
            </select>
          </div>
          <div>
            <label for="folder">Folder</label>
            <input name="folder" value="{{ active_folder }}" placeholder="." />
          </div>
        </div>
        <label for="question">Ask Scribe</label>
        <textarea name="question" rows="4" placeholder="What would you like to know about this project?"></textarea>
        <button type="submit">✨ Get Scribe Answer</button>
      </form>
    </div>

    <div class="layout">
      <aside class="panel">
        <h2>📂 Project Tree</h2>
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
          <h2>💬 Scribe Response</h2>
          <pre>{{ answer }}</pre>
        </div>

        <div class="panel">
          <h2>📋 Project Overview</h2>
          <pre>{{ overview }}</pre>
        </div>

        <div class="panel">
          <h2>🧠 Session Memory</h2>
          <pre>{{ memory }}</pre>
        </div>
      </div>
    </div>
  </body>
</html>
"""


def render_page(answer: str = "Ask Scribe a question to see the repo-grounded answer.", active_session: str = "default", active_folder: str = "."):
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
        answer = f"📄 {file_path}\n\n" + (content[:5000] if content else "(empty file)")
    else:
        answer = f"📄 {file_path}\n\nFile not found or not readable."
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
    print("🖊️  Scribe Web UI starting at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)

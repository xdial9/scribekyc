# 🖊️ Scribe

**Scribe** is a local-first CLI assistant that searches your notes or code and answers questions grounded in your own files. No account, no cloud — everything stays on your machine unless you optionally plug in Ollama or OpenAI for smarter answers.

## What it does

- 🔍 Ask questions grounded in your files (`ask`)
- 🔎 Keyword search across everything (`search`)
- 📝 Summarize a file or a whole directory (`summary`)
- 🔀 Compare two files by their vocabulary (`compare`)
- 📂 List what Scribe can see (`list`, `overview`)
- 💬 Interactive chat mode with named sessions (`chat`, `--session`)
- 🧠 Remembers recent questions per folder (`memory`, `sessions`)
- 🌐 Optional web UI for browsing, searching, and asking (`scribe_web.py`)

## Installation

Requirements: Python 3.8+.

```bash
git clone https://github.com/xjess5237-blip/scribekyc.git
cd scribekyc
chmod +x setup.sh
./setup.sh
```

This installs dependencies (`requests`, only needed for Ollama/OpenAI answers) and puts a `scribe` command on your PATH via `~/.local/bin`. If your shell doesn't find it afterwards, add this to your `~/.zshrc` or `~/.bashrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Quick start

Point Scribe at any folder with `--repo` (defaults to the folder you're in):

```bash
cd ~/my-notes

# Build the index (also rebuilt automatically when missing)
scribe index

# Ask questions
scribe ask "how does auth work?"

# Keep separate chat threads
scribe ask "first question" --session research
scribe ask "follow-up question" --session research

# Keyword search
scribe search "authentication"

# Summarize a file or directory
scribe summary README.md
scribe summary docs/

# Compare two files
scribe compare draft-v1.md draft-v2.md

# See what's indexed
scribe list
scribe overview

# Recent questions and sessions
scribe memory
scribe sessions

# Interactive mode
scribe chat
scribe chat --session research
```

Target another folder without `cd`:

```bash
scribe --repo ~/projects/myapp ask "where is the login handler?"
```

## Web UI

No extra dependencies — it uses only the Python standard library:

```bash
python3 scribe_web.py --repo ~/my-notes --port 5000
```

Then open http://localhost:5000. You get a file tree, full-text search, a file viewer, and the same Q&A as the terminal.

## Configuration (optional)

Without any configuration, Scribe answers offline using keyword-grounded extracts from your files. For LLM-written answers, set one of these (copy `.env.example` to `.env`, or export them):

```bash
# Ollama (local models)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

# ...or OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Ollama is tried first, then OpenAI, then offline mode.

## Commands reference

| Command    | Usage                  | Example                              |
|------------|------------------------|--------------------------------------|
| `ask`      | Ask a question         | `scribe ask "how does auth work?"`   |
| `chat`     | Interactive chat       | `scribe chat --session research`     |
| `search`   | Keyword search         | `scribe search "authentication"`     |
| `summary`  | Summarize file or dir  | `scribe summary docs/`               |
| `compare`  | Compare two files      | `scribe compare a.md b.md`           |
| `list`     | List indexed files     | `scribe list`                        |
| `overview` | Repo stats and files   | `scribe overview`                    |
| `memory`   | Recent questions       | `scribe memory`                      |
| `sessions` | List chat sessions     | `scribe sessions`                    |
| `index`    | Rebuild the index      | `scribe index`                       |

Global options: `--repo PATH` (or `-r`) before the command to target a folder; `--help` on any command.

## How it works

1. `scribe index` walks the target folder (skipping `.git`, virtualenvs, and Scribe's own bookkeeping files), chunks readable files (`.md .txt .csv .json .yaml .yml .py .js .ts .sh`), and writes `.scribe_index.json` next to your files.
2. Every question/search ranks those chunks by keyword and synonym overlap and shows the best matches.
3. With Ollama/OpenAI configured, the top chunks are passed to the model for a written answer; otherwise you get the grounded extracts directly.
4. Questions, answers, and session threads are stored as `.scribe_memory.json` / `.scribe_sessions.json` in the target folder. Re-run `index` after adding or changing files.

## Files in this repo

| File            | What it is                                              |
|-----------------|---------------------------------------------------------|
| `app.py`        | The whole CLI: indexing, search, Q&A, chat, sessions     |
| `scribe_web.py` | Optional web UI (stdlib only, no Flask needed)           |
| `setup.sh`      | Installer: dependencies + the `scribe` command          |
| `requirements.txt` | `requests` (only needed for Ollama/OpenAI answers)   |
| `.env.example`  | Optional model configuration template                   |
| `.gitignore`    | Keeps Scribe's local index/memory/session files uncommitted |

## Notes

- Scribe only reads inside the target folder — paths like `../../secret` are rejected.
- Scribe's own `.scribe_*.json` files are never indexed or listed, and are git-ignored.
- Works best on folders with real text content: notes, docs, research, code.
- Nothing leaves your machine unless you configure an external model.

## Happy scribing! 🎉

# 🖊️ Scribe

**Scribe** is a repo-grounded local AI assistant designed to help you explore, understand, and work with your projects.

## What is Scribe?

Scribe is:
- **Local first** — All data stays on your machine
- **Repo-aware** — Answers questions grounded in your project files
- **Session-aware** — Remembers context across chat turns
- **Terminal-first** — Easy to use from the command line
- **Browser-ready** — Optional web UI for visual exploration
- **Pluggable** — Works with Ollama or OpenAI if you have models available

## Features

- 🔍 Ask repo-grounded questions
- 🔎 Search by keyword
- 📝 Summarize files and directories
- 🔀 Compare files by overlapping terms
- 💬 Interactive terminal chat mode
- 🧠 Persistent session memory across turns
- 📊 Project overview and structure visualization
- 🌐 Optional web UI with folder tree navigation
- ⚡ Optional model-backed answers via Ollama or OpenAI

## Quick Start

### Installation

```bash
git clone <repo>
cd scribe
chmod +x setup.sh
./setup.sh
source ~/.zshrc  # or ~/.bashrc / ~/.bash_profile
```

### Usage

**Terminal mode:**
```bash
scribe chat
```

**One-shot question:**
```bash
scribe ask "what is this repo about?"
```

**With sessions:**
```bash
scribe ask "first question" --session research
scribe ask "follow-up question" --session research
```

**Search:**
```bash
scribe search "liveness"
```

**Summarize:**
```bash
scribe summary README.md
scribe summary research/vendors
```

**Compare files:**
```bash
scribe compare file_a.txt file_b.txt
```

**List directory:**
```bash
scribe list research/
```

**Show memory:**
```bash
scribe memory
```

**Project overview:**
```bash
scribe overview
```

**List sessions:**
```bash
scribe sessions
```

**Rebuild index:**
```bash
scribe index
```

### Web UI

```bash
python scribe_web.py
```

Then open http://localhost:5000

## Configuration (Optional)

Create a `.env` file in the Scribe directory for optional model support:

```bash
# For OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# For Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

If no model is configured, Scribe falls back to fast, offline repo-grounded search.

## Commands Reference

| Command | Usage | Example |
|---------|-------|----------|
| ask | Ask a question | `scribe ask "how does auth work?"` |
| chat | Interactive chat | `scribe chat` |
| search | Search repo | `scribe search "authentication"` |
| summary | Summarize file/dir | `scribe summary src/` |
| compare | Compare files | `scribe compare a.txt b.txt` |
| list | List directory | `scribe list research/` |
| overview | Show project overview | `scribe overview` |
| memory | Show chat history | `scribe memory` |
| sessions | List chat sessions | `scribe sessions` |
| index | Rebuild repo index | `scribe index` |
| help | Show help | `scribe --help` |

## Architecture

Scribe is built from three components:

1. **scribe_cli.py** — The core CLI and indexing engine
2. **scribe_web.py** — Optional Flask web UI
3. **scribe** — Executable wrapper for PATH integration

When you run `scribe ask "question"`, Scribe:
1. Loads the indexed repo chunks
2. Ranks them by relevance to your question
3. Optionally passes top matches to an LLM (Ollama/OpenAI)
4. Returns an answer grounded in your project files
5. Saves the turn to your session memory

## Notes

- Scribe works best on projects with good documentation and clear file structure
- The first run indexes your repo (takes a few seconds)
- All chat history and sessions are stored locally
- No data is sent anywhere unless you configure external models
- Perfect for research corpora, project notes, vendor analysis, and internal knowledge bases

## Happy Scribing! 🎉

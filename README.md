# Local AI Assistant

A terminal-first, repo-grounded assistant for working with local project files.

## Features
- Ask repo-grounded questions
- Search the repo by keyword
- Summarize a file or directory
- Compare two files by overlapping terms
- Interactive terminal chat mode
- Persistent memory of recent questions and answers
- Repo overview command to summarize the project structure
- Session-aware context across multiple chat turns
- Optional model-backed answers via Ollama or OpenAI
- Small Flask web UI for local browser access with a folder tree and session selector

## Quick start

```bash
python assistant_cli.py chat
```

```bash
python assistant_cli.py ask "what is this repo about?"
```

```bash
python assistant_cli.py overview
```

```bash
python assistant_cli.py search "liveness"
```

```bash
python assistant_cli.py summary README.md
```

```bash
python assistant_cli.py compare research/vendors/vendor_jumio.txt research/vendors/vendor_au10tix.txt
```

```bash
python assistant_cli.py list research/vendors
```

## Session support

You can keep a coherent chat thread with a named session:

```bash
python assistant_cli.py ask "what is the repo about?" --session research
python assistant_cli.py ask "compare the vendor files" --session research
```

## Index refresh

```bash
python assistant_cli.py index
```

## Web app

```bash
python app.py
```

Then open http://localhost:5000

## Optional model support

If you want model-backed answers, copy the environment example and set values:

```bash
cp .env.example .env
```

Then set either:
- `OPENAI_API_KEY` and `OPENAI_MODEL`
- or `OLLAMA_HOST` and `OLLAMA_MODEL`

If no model is configured, the assistant falls back to offline repo-grounded search.

## Notes

This assistant is designed to be grounded in your local repo and useful for project documentation, note-taking, research corpora, and internal knowledge bases.

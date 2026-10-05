#!/usr/bin/env bash
#
# Scribe setup — installs dependencies and the `scribe` command.
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
#
set -euo pipefail

cd "$(dirname "$0")"

echo "→ Checking Python dependencies..."
if python3 -c "import requests" 2>/dev/null; then
    echo "  requests already installed — skipping."
else
    echo "  installing requests..."
    if ! python3 -m pip install -r requirements.txt 2>/dev/null; then
        echo "  system pip is locked (PEP 668) — retrying with --break-system-packages..."
        python3 -m pip install --break-system-packages -r requirements.txt \
            || echo "  WARNING: could not install requests. Offline mode still works fine; only Ollama/OpenAI answers need it."
    fi
fi

echo "→ Installing the 'scribe' command..."
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
ln -sf "$(pwd)/app.py" "$BIN_DIR/scribe"
chmod +x "$(pwd)/app.py" "$(pwd)/scribe_web.py"

echo ""
echo "Done. 'scribe' is installed at $BIN_DIR/scribe"
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "Add this to your ~/.zshrc or ~/.bashrc so your shell finds it:"
    echo "    export PATH=\"$BIN_DIR:\$PATH\""
    echo ""
    echo "Then reload your shell and try:  scribe --help"
else
    echo "Try it:  scribe --help"
fi

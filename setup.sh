#!/bin/bash

# Scribe Installation Script
# This script adds scribe to your PATH so you can run it from anywhere

set -e

echo "🖊️  Setting up Scribe..."

SCRIBE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Scribe directory: $SCRIBE_DIR"

# Make the scribe executable
chmod +x "$SCRIBE_DIR/scribe"

# Detect shell config file
if [[ -f "$HOME/.zshrc" ]]; then
    SHELL_RC="$HOME/.zshrc"
elif [[ -f "$HOME/.bashrc" ]]; then
    SHELL_RC="$HOME/.bashrc"
elif [[ -f "$HOME/.bash_profile" ]]; then
    SHELL_RC="$HOME/.bash_profile"
else
    echo "⚠️  Could not find shell configuration file (.zshrc, .bashrc, or .bash_profile)"
    echo "Please manually add this to your shell configuration:"
    echo "export PATH=\"$SCRIBE_DIR:\$PATH\""
    exit 1
fi

# Add to PATH if not already there
if ! grep -q "export PATH=.*$SCRIBE_DIR" "$SHELL_RC"; then
    echo "export PATH=\"$SCRIBE_DIR:\$PATH\"" >> "$SHELL_RC"
    echo "✅ Added Scribe to PATH in $SHELL_RC"
else
    echo "✅ Scribe is already in PATH"
fi

echo ""
echo "📦 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Reload your shell: source $SHELL_RC"
echo "2. Try it out: scribe ask 'what is this repo?'"
echo "3. Interactive mode: scribe chat"
echo "4. Web UI: python $SCRIBE_DIR/scribe_web.py"
echo ""
echo "Happy scribing! 🎉"

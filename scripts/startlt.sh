#!/usr/bin/env bash
# One-time setup: creates the venv, installs livetree in editable mode,
# and symlinks `lt` into ~/.local/bin so it is available globally without
# activating the venv.  Re-run after a fresh clone or if the venv is deleted.
# No need to re-run after a reboot — the symlink and venv persist.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$REPO/.venv"
BIN="$HOME/.local/bin"

if [ ! -d "$VENV" ]; then
    echo "Creating venv..."
    python3 -m venv "$VENV"
fi

echo "Installing livetree (editable)..."
"$VENV/bin/pip" install --quiet -e "$REPO"

mkdir -p "$BIN"
ln -sf "$VENV/bin/lt" "$BIN/lt"
echo "Linked: $BIN/lt -> $VENV/bin/lt"

if [[ ":$PATH:" != *":$BIN:"* ]]; then
    echo ""
    echo "Warning: $BIN is not in your PATH."
    echo "Add this line to your ~/.zshrc:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo "Then open a new terminal."
fi

echo "Done. Run: lt ."

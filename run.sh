#!/usr/bin/env bash
# run.sh — set up .venv (Python 3.13) via uv and launch UltimatePyve.
#
# Idempotent: first run creates .venv and installs dependencies; subsequent
# runs skip setup if deps are already satisfied.
#
# The container-owned .venv-mcp/ (used by mcp-build for headless tests) is a
# separate venv — see claude/docs/PYTHON_GENERAL.md.

set -euo pipefail

cd "$(dirname "$0")"

# --- Locate uv --------------------------------------------------------------
if command -v uv >/dev/null 2>&1; then
    UV=uv
elif [ -x "$HOME/.local/bin/uv" ]; then
    UV="$HOME/.local/bin/uv"
else
    echo "Error: uv not installed. Install with:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# --- Create venv if missing -------------------------------------------------
if [ ! -d .venv ]; then
    echo ">> Creating .venv with Python 3.13 (uv will download if needed)..."
    "$UV" venv --python 3.13 .venv
fi

# --- Install/sync runtime deps (fast if already satisfied) ------------------
echo ">> Syncing dependencies from requirements.txt..."
"$UV" pip install --python .venv/bin/python -r requirements.txt

# --- Launch -----------------------------------------------------------------
echo ">> Starting UltimatePyve..."
exec .venv/bin/python main.py "$@"

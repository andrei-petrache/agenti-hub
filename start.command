#!/bin/bash
# BuzzzHub on macOS: double-click this file.
# The first time it creates a private Python environment (.venv) and installs pywebview; after that it just starts.
cd "$(dirname "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found. Install it from https://www.python.org/downloads/macos/ and try again."
  read -r -p "Press Enter to close..."
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "First start: preparing the Python environment (takes about a minute)..."
  python3 -m venv .venv || exit 1
  .venv/bin/python -m pip install --quiet --upgrade pip
  .venv/bin/python -m pip install --quiet -r requirements.txt || exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "Note: the 'claude' command is not on PATH; live status and messages will not work."
fi

exec .venv/bin/python app.py

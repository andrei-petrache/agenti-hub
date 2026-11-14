#!/bin/bash
# BuzzzHub pe macOS: dublu-click pe acest fișier.
# Prima dată își face un mediu Python separat (.venv) și instalează pywebview; apoi doar pornește.
cd "$(dirname "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo "Nu găsesc python3. Instalează-l de pe https://www.python.org/downloads/macos/ și încearcă din nou."
  read -r -p "Apasă Enter ca să închizi..."
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "Prima pornire: pregătesc mediul Python (durează un minut)..."
  python3 -m venv .venv || exit 1
  .venv/bin/python -m pip install --quiet --upgrade pip
  .venv/bin/python -m pip install --quiet -r requirements.txt || exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "Atenție: nu găsesc comanda 'claude' în PATH; stările live și mesajele nu vor merge."
fi

exec .venv/bin/python app.py

#!/usr/bin/env bash
# Job Hunter launcher — macOS double-click
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

if ! command -v python3 &>/dev/null; then
    osascript -e 'display alert "Python 3 Required" message "Install Python 3 from https://python.org"'
    exit 1
fi

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -q -r requirements.txt
    playwright install chromium 2>/dev/null || true
else
    source .venv/bin/activate
fi

python3 app.py

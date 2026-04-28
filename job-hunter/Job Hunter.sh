#!/usr/bin/env bash
# Job Hunter launcher — Linux/macOS
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

if ! command -v python3 &>/dev/null; then
    echo "Python 3 is required. Install from https://python.org" >&2
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment…"
    python3 -m venv .venv
    source .venv/bin/activate
    echo "Installing dependencies…"
    pip install -q -r requirements.txt
    echo "Installing Playwright browser…"
    playwright install chromium 2>/dev/null || true
else
    source .venv/bin/activate
fi

python3 app.py "$@"

#!/bin/bash
# Intel Platform — macOS double-click launcher
# Right-click → Open the first time to bypass Gatekeeper
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v python3 &>/dev/null; then
    osascript -e 'display alert "Python 3 Required" message "Install Python 3.9+ from python.org then try again."'
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "First-time setup — installing dependencies (2-3 min)..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt -q
    echo "Setup complete!"
else
    source .venv/bin/activate
fi

python3 app.py

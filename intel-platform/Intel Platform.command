#!/bin/bash
# Intel Platform — macOS double-click launcher
# Right-click → Open the first time to bypass Gatekeeper

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Find Python 3 with tkinter (python.org or Homebrew)
PYTHON=""
for candidate in python3.12 python3.11 python3.10 python3.9 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
        if "$candidate" -c "import tkinter" 2>/dev/null; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    osascript -e 'display alert "Python 3 + Tk Required" message "Install Python from python.org (includes Tk built-in), or run: brew install python-tk@3.12"'
    exit 1
fi

echo "Using $PYTHON"

if [ ! -d ".venv" ]; then
    echo "First-time setup — installing dependencies (2-3 min)..."
    "$PYTHON" -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    echo "Setup complete!"
else
    source .venv/bin/activate
fi

python app.py

#!/bin/bash
# Intel Platform — Linux double-click launcher
# Make executable: chmod +x "Intel Platform.sh"
# Then double-click in your file manager (set to "Run" not "Display")

cd "$(dirname "$(readlink -f "$0")")"

# Find a Python 3 that has tkinter
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
    echo "ERROR: No Python 3 with tkinter found."
    echo "Fix with one of:"
    echo "  Ubuntu/Debian: sudo apt install python3-tk"
    echo "  Fedora:        sudo dnf install python3-tkinter"
    echo "  Arch:          sudo pacman -S tk"
    read -p "Press Enter to exit..."
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

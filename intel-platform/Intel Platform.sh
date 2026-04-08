#!/bin/bash
# Intel Platform — Linux double-click launcher
# Make executable: chmod +x "Intel Platform.sh"
# Then double-click in your file manager (set to "Run" not "Display")
cd "$(dirname "$(readlink -f "$0")")"

command -v python3 >/dev/null 2>&1 || {
    echo "Python 3 is required. Install with: sudo apt install python3 python3-venv"
    read -p "Press Enter to exit..."
    exit 1
}

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

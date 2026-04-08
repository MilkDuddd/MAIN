@echo off
:: Intel Platform — Windows double-click launcher
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo Python not found. Please install Python 3.9+ from python.org
    pause
    exit /b 1
)

if not exist ".venv\" (
    echo First-time setup - installing dependencies (2-3 min)...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt -q
    echo Setup complete!
) else (
    call .venv\Scripts\activate.bat
)

pythonw app.py

@echo off
:: Intel Platform — Windows double-click launcher
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo Python not found.
    echo Install Python 3.9+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

if not exist ".venv\" (
    echo First-time setup - installing dependencies (this takes 2-3 minutes^)...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt -q
    if errorlevel 1 (
        echo Failed to install dependencies.
        pause
        exit /b 1
    )
    echo Setup complete.
) else (
    call .venv\Scripts\activate.bat
)

pythonw app.py

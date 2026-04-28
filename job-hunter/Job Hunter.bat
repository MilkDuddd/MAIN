@echo off
:: Job Hunter launcher — Windows
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo Python 3 is required. Install from https://python.org
    pause
    exit /b 1
)

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -q -r requirements.txt
    playwright install chromium
) else (
    call .venv\Scripts\activate.bat
)

python app.py
pause

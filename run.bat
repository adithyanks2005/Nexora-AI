@echo off
echo Starting Nexora AI...
cd /d "%~dp0"
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt -q
echo.
echo Nexora AI is running at http://localhost:8000
echo Press Ctrl+C to stop.
echo.
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

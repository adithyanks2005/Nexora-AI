@echo off
echo Setting up Nexora AI...
cd /d "%~dp0"
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt
if not exist ".env" (
    copy .env.example .env
    echo.
    echo IMPORTANT: Open .env and add your ANTHROPIC_API_KEY
)
echo.
echo Setup complete! Run: run.bat
pause

@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating local app environment...
  python -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Add your GROQ_API_KEY to .env before using AI chat.
)

python desktop_app.py

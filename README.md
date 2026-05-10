# 🧬 Nexora AI — Healthcare Chatbot

An advanced AI-powered healthcare assistant with chat, symptom analysis, health calculators, medication reminders, and health record tracking.

**Author:** ADITHYAN KS

## Features

| Feature | Description |
|---|---|
| 💬 AI Chat | Conversational health assistant powered by OpenRouter with a Claude-style model and full chat history |
| 🩺 Symptom Checker | AI-powered symptom analysis with body area, severity & duration context |
| 🧮 Health Calculators | BMI, Daily Calories (with macros), Water Intake, Ideal Body Weight |
| ⏰ Medication Reminders | Add, toggle, and manage health reminders with icons |
| 📋 Health Records | Log and track blood pressure, sugar, weight, heart rate, mood, and more |
| 🎤 Voice Input | Speak your health questions directly |
| 🌙 Dark / Light Mode | Toggle between themes |
| 📱 Responsive | Works on desktop and mobile |

## Tech Stack

- **Backend**: FastAPI + Uvicorn
- **AI**: OpenRouter (`anthropic/claude-sonnet-4.6` by default)
- **Database**: SQLite (chat history, reminders, health records)
- **Frontend**: Vanilla HTML / CSS / JavaScript (no framework needed)
- **Tests**: Pytest

## Quick Start

### 1. Get an OpenRouter API Key
Create an API key in [OpenRouter](https://openrouter.ai/settings/keys).

### 2. Setup

```bash
cd nexora-ai
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

Or just double-click **`setup.bat`** on Windows.

### 3. Run

```bash
uvicorn backend.main:app --reload --port 8000
```

Or double-click **`run.bat`** on Windows.

Open **http://localhost:8000** in your browser.

## Project Structure

```
nexora-ai/
├── backend/
│   ├── main.py          # FastAPI routes
│   ├── ai.py            # OpenRouter AI integration
│   ├── calculators.py   # Health calculators
│   ├── database.py      # SQLite setup
│   └── models.py        # Pydantic models
├── frontend/
│   ├── index.html       # Single-page app
│   └── static/
│       ├── css/style.css
│       └── js/app.js
├── tests/
│   └── test_api.py      # Full test suite
├── data/                # SQLite database (auto-created)
├── .env.example
├── requirements.txt
├── setup.bat
└── run.bat
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET/POST | `/api/sessions` | Chat sessions |
| DELETE | `/api/sessions/{id}` | Delete session |
| GET | `/api/sessions/{id}/messages` | Session messages |
| POST | `/api/chat` | Send chat message |
| POST | `/api/symptoms` | Analyze symptoms |
| POST | `/api/calc/bmi` | BMI calculator |
| POST | `/api/calc/calories` | Calorie calculator |
| POST | `/api/calc/water` | Water intake calculator |
| POST | `/api/calc/ideal-weight` | Ideal weight calculator |
| GET/POST | `/api/reminders` | Reminders CRUD |
| PATCH | `/api/reminders/{id}/toggle` | Toggle reminder done |
| DELETE | `/api/reminders/{id}` | Delete reminder |
| DELETE | `/api/reminders/done/clear` | Clear done reminders |
| GET/POST | `/api/records` | Health records |
| DELETE | `/api/records/{id}` | Delete record |

## Running Tests

```bash
pytest tests/ -v
```

## Disclaimer

Nexora AI provides general health information only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider for medical concerns.

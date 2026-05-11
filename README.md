# Nexora AI - Healthcare Chatbot

An advanced AI-powered healthcare assistant with chat, symptom analysis, health calculators, medication reminders, and health record tracking.

> Created by **ADITHYAN KS**

## Features

| Feature | Description |
|---|---|
| AI Chat | Conversational health assistant powered by OpenRouter with a Claude-style model and full chat history |
| Symptom Checker | AI-powered symptom analysis with body area, severity, and duration context |
| Health Calculators | BMI, daily calories with macros, water intake, and ideal body weight |
| Medication Reminders | Add, toggle, and manage health reminders with icons |
| Health Records | Log and track blood pressure, sugar, weight, heart rate, mood, and more |
| Voice Input | Speak your health questions directly |
| Dark / Light Mode | Toggle between themes |
| Responsive UI | Works on desktop and mobile |

## Tech Stack

- **Backend**: FastAPI + Uvicorn
- **AI**: OpenRouter (`anthropic/claude-sonnet-4.6` by default)
- **Database**: SQLite for chat history, reminders, and health records
- **Frontend**: Vanilla HTML, CSS, and JavaScript
- **Tests**: Pytest
- **Deployment**: Render Blueprint via `render.yaml`

## Quick Start

### 1. Get an OpenRouter API Key

Create an API key in [OpenRouter](https://openrouter.ai/settings/keys).

### 2. Setup

```bash
cd nexora-ai
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and add your key:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=anthropic/claude-sonnet-4.6
```

### 3. Run

```bash
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001
```

Open [http://127.0.0.1:8001](http://127.0.0.1:8001) in your browser.

## App Install Options

### Install from the live site

Open the deployed site in Chrome, Edge, or another PWA-capable browser and use the app install prompt or browser menu to install **Nexora AI**.

### Run as a local Windows app

After downloading the GitHub ZIP, extract it and double-click:

```text
run_app.bat
```

The launcher creates the Python environment if needed, installs dependencies, and opens Nexora AI locally. Add your OpenRouter key to `.env` before using AI chat.

### Optional desktop EXE build

```bash
pip install -r requirements-desktop.txt
pyinstaller --onefile --name NexoraAI desktop_app.py
```

The generated executable will be in `dist/`.

## Project Structure

```text
nexora-ai/
├── backend/
│   ├── main.py          # FastAPI routes
│   ├── ai.py            # OpenRouter AI integration
│   ├── calculators.py   # Health calculators
│   ├── database.py      # SQLite setup
│   └── models.py        # Pydantic models
├── frontend/
│   ├── index.html       # Single-page app
│   ├── manifest.webmanifest
│   ├── service-worker.js
│   └── static/
│       ├── css/style.css
│       ├── icons/icon.svg
│       └── js/app.js
├── tests/
│   └── test_api.py
├── data/
├── .env.example
├── render.yaml
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

## Deploy

This project includes a Render Blueprint:

```text
render.yaml
```

After pushing to GitHub, open:

[Render Blueprint Deploy](https://dashboard.render.com/blueprint/new?repo=https://github.com/adithyanks2005/Nexora-AI)

Set these environment variables in Render:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=anthropic/claude-sonnet-4.6
```

## Running Tests

```bash
pytest tests/ -v
```

## Disclaimer

Nexora AI provides general health information only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider for medical concerns.

## Author

**ADITHYAN KS**

## License

MIT License. See [LICENSE](LICENSE).

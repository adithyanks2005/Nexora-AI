# Project Structure

## Directory Layout

```
nexora-ai/
├── backend/                      # FastAPI backend application
│   ├── main.py                  # Application entry point
│   ├── ai.py                    # AI/LLM integration
│   ├── chat.py                  # Chat endpoints
│   ├── database.py              # Database operations
│   ├── models.py                # Pydantic models
│   ├── calculators.py           # Health calculators
│   ├── reminders.py             # Reminder management
│   ├── history.py               # Chat history
│   └── __init__.py
│
├── frontend/                     # Web UI
│   ├── index.html               # Main HTML file
│   ├── manifest.webmanifest     # PWA manifest
│   ├── service-worker.js        # Service worker
│   └── static/
│       ├── css/
│       │   └── style.css        # Stylesheet
│       ├── js/
│       │   └── app.js           # Main application script
│       └── icons/               # App icons
│
├── tests/                        # Test suite
│   ├── test_api.py              # API tests
│   └── __init__.py
│
├── data/                         # Data storage (generated)
│   └── app.db                   # SQLite database
│
├── Configuration Files
│   ├── .env                     # Environment variables (local)
│   ├── .env.example             # Example env template
│   ├── .gitignore               # Git ignore rules
│   ├── requirements.txt         # Python dependencies
│   ├── render.yaml              # Render deployment config
│   ├── vercel.json              # Vercel deployment config
│   └── package.json             # Node metadata (optional)
│
├── Documentation
│   ├── README.md                # Project overview
│   ├── PROJECT_STRUCTURE.md     # This file
│   └── LICENSE                  # MIT License
│
└── Utility Scripts
    ├── setup.bat                # Windows setup script
    ├── run.bat                  # Windows run script
    └── desktop_app.py           # Desktop application launcher
```

## Key Files

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI application root, route definitions |
| `backend/ai.py` | Groq API integration, LLM calls |
| `backend/database.py` | SQLite database initialization and queries |
| `frontend/index.html` | Single-page application entry point |
| `frontend/static/js/app.js` | Main frontend logic |
| `.env.example` | Template for environment configuration |
| `requirements.txt` | Python package dependencies |
| `render.yaml` | Render.com deployment blueprint |
| `vercel.json` | Vercel deployment configuration |

## Development Workflow

```bash
# Setup
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Run locally
uvicorn backend.main:app --reload

# Testing
pytest

# Deployment
# Render: Push to main branch (configured via render.yaml)
# Vercel: Connect repo and deploy (uses vercel.json)
```

## Environment Variables

Required in `.env`:
- `GROQ_API_KEY` - API key from Groq
- `GROQ_MODEL` - Model ID (default: `llama-3.1-8b-instant`)

## Deployment

- **Local**: Run with `uvicorn backend.main:app`
- **Render**: Automatic via `render.yaml` blueprint
- **Vercel**: Automatic via `vercel.json` configuration

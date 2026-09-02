# MediCura AI - AI Healthcare Assistant

> **Free AI-powered healthcare assistant with symptom checker, health calculators, medication reminders, and health record tracking**

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://nexora-ai-flax.vercel.app)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Created by **Adithyan KS**

---

## ✨ Features

- 🤖 **AI Health Chat** - Conversational assistant powered by Groq Llama 3.1
- 🏥 **Symptom Checker** - AI-powered symptom analysis with context
- 📊 **Health Calculators** - BMI, calories, water intake, ideal weight
- 💊 **Medication Reminders** - Track and manage your medications
- 📋 **Health Records** - Log vitals (BP, sugar, weight, heart rate)
- 🎤 **Voice Input** - Speak your health questions
- 🌓 **Dark/Light Mode** - Choose your preferred theme
- 📱 **Progressive Web App** - Install as native app on any device
- 🔐 **Secure** - Google OAuth & guest mode authentication

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [Groq API Key](https://console.groq.com/keys) (free)

### Installation

```bash
# Clone repository
git clone https://github.com/adithyanks2005/Nexora-AI.git
cd Nexora-AI

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate  # On Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac
```

### Configuration

Edit `.env` file:

```env
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_CLIENT_ID=your_google_client_id (optional)
JWT_SECRET=your_random_secret_key

# Optional: Supabase for persistent storage
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_key
```

### Run Locally

```bash
# Quick start with batch file (Windows)
run.bat

# Or manually
python -m uvicorn backend.main:app --reload --port 8000
```

Visit: **http://localhost:8000**

---

## 📁 Project Structure

```
nexora-ai/
├── api/                    # Vercel serverless entry point
├── backend/                # Python FastAPI backend
│   ├── main.py            # Main application & routes
│   ├── ai.py              # Groq AI integration
│   ├── auth.py            # Authentication logic
│   ├── calculators.py     # Health calculators
│   ├── database.py        # Database access layer
│   ├── models.py          # Pydantic models
│   └── config.py          # Configuration management
├── frontend/              # Static frontend
│   ├── index.html        # Single-page application
│   ├── static/           # CSS, JS, icons
│   ├── service-worker.js # PWA service worker
│   └── manifest.webmanifest
├── docs/                  # Documentation
│   ├── DEPLOYMENT.md     # Deployment guide
│   ├── SEO_GUIDE.md      # SEO & indexing
│   └── QUICK_START.md    # Getting started
├── tests/                 # Test suite
├── .env                   # Environment variables (not in git)
├── requirements.txt       # Python dependencies
├── package.json          # Node.js config (for Vercel)
├── vercel.json           # Vercel configuration
└── README.md             # This file
```

---

## 🌐 Deployment

### Deploy to Vercel (Recommended)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/adithyanks2005/Nexora-AI)

1. Click the deploy button above
2. Connect your GitHub account
3. Add environment variables:
   - `GROQ_API_KEY`
   - `GOOGLE_CLIENT_ID`
   - `JWT_SECRET`
4. Deploy!

**See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions**

---

## 🔧 Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI + Uvicorn |
| **AI Model** | Groq (Llama 3.1 8B) |
| **Database** | SQLite (local) / Supabase (production) |
| **Frontend** | Vanilla HTML/CSS/JavaScript |
| **Auth** | Google OAuth / JWT |
| **Deployment** | Vercel Serverless Functions |
| **PWA** | Service Worker + Web Manifest |

---

## 📚 Documentation

- 📖 [Deployment Guide](docs/DEPLOYMENT.md) - Deploy to Vercel
- 🔍 [SEO Guide](docs/SEO_GUIDE.md) - Get indexed on Google
- 🚀 [Quick Start](docs/QUICK_START.md) - Detailed setup
- 📝 [Changelog](docs/CHANGELOG.md) - Version history
- 🌐 [Domain Setup](docs/DOMAIN_SETUP.md) - Custom domain

---

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest --cov=backend tests/
```

---

## 🛡️ Security Features

- 🔒 HTTPS enforced (via Vercel)
- 🛡️ Security headers (CSP, HSTS, X-Frame-Options)
- ⚡ Rate limiting (30 req/min per endpoint)
- 🔐 JWT-based authentication
- 🚫 Protected API documentation endpoints

---

## 📱 Progressive Web App

Install as a native app:

1. Visit the website
2. Click "Install" prompt (Chrome/Edge)
3. Or: Menu → "Install App"
4. Access from home screen like any app!

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## ⚠️ Medical Disclaimer

**MediCura AI provides general health information only.**

This application is NOT a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider for medical concerns. Never disregard professional medical advice or delay seeking it because of information from this app.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Adithyan KS**

- GitHub: [@adithyanks2005](https://github.com/adithyanks2005)
- Project: [Nexora AI](https://github.com/adithyanks2005/Nexora-AI)

---

## 🌟 Support

If you find this project helpful, please give it a ⭐ on GitHub!

**Live Demo:** [https://nexora-ai-flax.vercel.app](https://nexora-ai-flax.vercel.app)

# Clean Project Structure

## ✅ Current Organization

```
nexora-ai/
│
├── 📁 .github/                # GitHub configuration
│   ├── modernize/             # Modernization workflows
│   └── workflows/             # CI/CD workflows
│
├── 📁 android/                # Android app build
│   ├── app/                   # Android application
│   ├── gradle/                # Gradle wrapper
│   ├── build.gradle           # Build configuration
│   └── *.bat                  # Build scripts
│
├── 📁 api/                    # Vercel serverless entry
│   └── index.py               # Entry point for Vercel
│
├── 📁 backend/                # Python backend
│   ├── main.py                # FastAPI application & routes
│   ├── ai.py                  # Groq AI integration
│   ├── auth.py                # Authentication (Google OAuth, JWT)
│   ├── calculators.py         # Health calculators (BMI, calories, etc.)
│   ├── config.py              # Configuration management
│   ├── crawler.py             # Web crawler utility
│   ├── database.py            # Database access (SQLite/Supabase)
│   ├── models.py              # Pydantic data models
│   ├── schema.sql             # SQLite schema
│   └── __init__.py
│
├── 📁 data/                   # Local SQLite database (gitignored)
│   └── nexora.db              # Local development database
│
├── 📁 docs/                   # 📚 All documentation
│   ├── DEPLOYMENT.md          # Deployment to Vercel guide
│   ├── SEO_GUIDE.md           # Google indexing & SEO
│   ├── QUICK_START.md         # Getting started guide
│   ├── CHANGELOG.md           # Project history & improvements
│   └── DOMAIN_SETUP.md        # Custom domain configuration
│
├── 📁 frontend/               # Static frontend
│   ├── index.html             # Main SPA
│   ├── service-worker.js      # PWA service worker
│   ├── manifest.webmanifest   # PWA manifest
│   ├── robots.txt             # SEO crawl rules
│   ├── sitemap.xml            # SEO sitemap
│   ├── llms.txt               # LLM documentation
│   ├── .well-known/           # Domain verification
│   │   └── assetlinks.json    # Android TWA config
│   └── static/                # Static assets
│       ├── css/               # Stylesheets
│       ├── js/                # JavaScript
│       └── icons/             # App icons & images
│
├── 📁 tests/                  # Test suite
│   └── test_api.py            # API tests
│
├── 📁 .venv/                  # Virtual environment (gitignored)
├── 📁 node_modules/           # Node packages (gitignored)
├── 📁 __pycache__/            # Python cache (gitignored)
│
├── 📄 .env                    # Environment variables (gitignored)
├── 📄 .gitignore              # Git ignore rules
├── 📄 .vercelignore           # Vercel ignore rules
│
├── 📄 LICENSE                 # MIT License
├── 📄 README.md               # Main documentation
├── 📄 PROJECT_STRUCTURE.md    # This file
│
├── 📄 package.json            # Node.js configuration (for Vercel)
├── 📄 requirements.txt        # Python dependencies
├── 📄 vercel.json             # Vercel deployment config
│
├── 📄 run.bat                 # Windows local dev script
│
└── 📄 BEFORE_AFTER_COMPARISON.md  # Legacy comparison
└── 📄 REBRAND_SUMMARY.md           # Rebrand history
```

## 🗂️ Directory Purposes

### `/api`
- Vercel serverless function entry point
- Imports and exports the FastAPI app
- Adds production security middleware

### `/backend`
- Core Python application logic
- FastAPI routes and business logic
- AI integration, auth, database access

### `/frontend`
- Static HTML/CSS/JavaScript
- Single-page application
- PWA configuration

### `/docs`
- **All** project documentation
- Deployment guides
- SEO and domain setup
- Change logs and history

### `/android`
- Android APK build configuration
- Trusted Web Activity (TWA) setup
- Google Play Store assets

### `/tests`
- pytest test suite
- API endpoint tests

## 📝 Key Files

| File | Purpose |
|------|---------|
| `README.md` | Main project documentation |
| `requirements.txt` | Python dependencies |
| `package.json` | Node/Vercel configuration |
| `vercel.json` | Vercel deployment config |
| `.env` | Environment variables (not in git) |
| `run.bat` | Quick local development |

## 🚫 Gitignored Items

- `.env` - Environment variables
- `.venv/` - Virtual environment
- `node_modules/` - Node packages
- `__pycache__/` - Python cache
- `data/` - Local database
- `.pytest_cache/` - Test cache
- `.uv-cache/` - UV cache
- `.vscode/` - Editor settings

## 🧹 Cleanup Completed

### Removed:
- ❌ 25+ duplicate documentation files
- ❌ Temporary build outputs
- ❌ One-time use scripts
- ❌ Random image files
- ❌ PR description files
- ❌ Duplicate .env files

### Consolidated:
- ✅ All deployment docs → `docs/DEPLOYMENT.md`
- ✅ All SEO guides → `docs/SEO_GUIDE.md`
- ✅ All quick starts → `docs/QUICK_START.md`
- ✅ All improvements → `docs/CHANGELOG.md`

## 📐 Design Principles

1. **Single Source of Truth** - One file per topic
2. **Clear Organization** - Logical directory structure
3. **No Duplicates** - Consolidated documentation
4. **Gitignore Properly** - No build artifacts or secrets
5. **Documentation in `/docs`** - Easy to find

## 🔄 Ongoing Maintenance

- Keep `/docs` as the single source for all documentation
- Delete temporary files immediately after use
- No duplicate files - consolidate instead
- Update `docs/CHANGELOG.md` with major changes
- Keep root directory clean - only essential config files

---

**Last Updated:** September 2, 2026  
**Cleanup By:** Kiro AI Assistant

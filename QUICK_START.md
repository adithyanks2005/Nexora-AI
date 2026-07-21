# Nexora AI - Quick Start Guide

## ✅ All Major Bugs Fixed!

The following critical bugs have been fixed:

1. ✅ **Sidebar HTML** - Fixed missing `</button>` tag and user profile layout
2. ✅ **Route Ordering** - `/api/reminders/done/clear` now registered before `/{rid}`
3. ✅ **Imperial BMI** - Height now correctly converted from inches to cm
4. ✅ **JWT Security** - Random secure secret generated if not configured
5. ✅ **Error Handling** - No more traceback leakage in responses
6. ✅ **Async Crawler** - Robots.txt check no longer blocks event loop
7. ✅ **Height Validation** - Ideal weight calculator validates minimum height
8. ✅ **API Error Handling** - Frontend properly handles 401 errors

See `FIXES_SUMMARY.md` for complete details.

---

## Local Development

### Prerequisites
- Python 3.10+ 
- `uv` package manager (recommended) or `pip`

### Setup

1. **Install dependencies:**
   ```bash
   # Using uv (recommended):
   uv sync
   
   # OR using pip:
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   # Copy template and edit
   copy .env.template .env  # Windows
   cp .env.template .env    # Linux/Mac
   ```

   **Required:**
   - `GROQ_API_KEY` - Get free key at https://console.groq.com/keys
   
   **Optional:**
   - `JWT_SECRET` - Will auto-generate if missing (32+ char random string recommended)
   - `GOOGLE_CLIENT_ID` - For Google OAuth (optional, guest login works without)

3. **Run the development server:**
   ```bash
   # Using the convenient batch file (Windows):
   run.bat
   
   # OR directly:
   uvicorn backend.main:app --reload --port 8000
   ```

4. **Open the app:**
   - http://localhost:8000

---

## Testing Your Fixes

```bash
# Run automated tests:
python test_fixes.py

# Expected output:
#   ✓ Imports OK
#   ✓ BMI metric: 24.2 (Normal Weight)
#   ✓ BMI imperial: 24.1 (Normal Weight)  
#   ✓ Ideal weight validation works
#   ✓ JWT secret is random
#   ✓ Route ordering correct
```

---

## Manual Testing Checklist

### Authentication
- [ ] Google login (if configured)
- [ ] Guest login  
- [ ] User profile displays in sidebar
- [ ] Sign out works

### Chat
- [ ] Send message to AI
- [ ] View chat history
- [ ] Create new chat session
- [ ] Delete chat session

### Features
- [ ] Symptom Checker analyzes symptoms
- [ ] BMI calculator (metric mode)
- [ ] BMI calculator (imperial mode - 154 lbs, 67 in = ~24.1 BMI)
- [ ] Calorie calculator
- [ ] Water intake calculator  
- [ ] Ideal weight calculator
- [ ] Add reminder
- [ ] Toggle reminder done
- [ ] Delete reminder
- [ ] Clear done reminders
- [ ] Add health record
- [ ] Delete health record

### Navigation
- [ ] All sidebar nav buttons work
- [ ] Clicking user profile doesn't navigate to Calculators
- [ ] Mobile sidebar toggle works

---

## Deployment to Vercel

### One-Time Setup

1. **Link your repo to Vercel:**
   ```bash
   # Install Vercel CLI
   npm install -g vercel
   
   # Deploy
   vercel
   ```

2. **Configure environment variables in Vercel Dashboard:**
   - Go to Project Settings → Environment Variables
   - Add these variables for **Production, Preview, Development**:
     ```
     GROQ_API_KEY=your_groq_key_here
     JWT_SECRET=your_32_char_random_string
     GOOGLE_CLIENT_ID=your_google_client_id (optional)
     ```

3. **For database persistence, set up Supabase:**
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   ```

### Deploy Updates

```bash
# Deploy to production
vercel --prod

# OR just push to main branch (auto-deploys if connected)
git push origin main
```

---

## Architecture Overview

### Frontend
- **`frontend/index.html`** - Complete SPA with inline JavaScript (ACTIVE)
- **`frontend/static/js/app.js`** - UNUSED orphaned code (can be deleted)
- **`frontend/static/css/style.css`** - Stylesheet

The app loads **only** `index.html` which contains all HTML, CSS, and JavaScript inline. The `app.js` file is never loaded and can be safely ignored or removed.

### Backend
- **`backend/main.py`** - FastAPI app, routes, middleware
- **`backend/database.py`** - Dual backend (SQLite/Supabase)
- **`backend/ai.py`** - Groq LLM integration
- **`backend/auth.py`** - JWT + Google OAuth
- **`backend/calculators.py`** - Health calculations
- **`backend/crawler.py`** - Web scraper
- **`backend/models.py`** - Pydantic schemas

### Data Storage
- **Local dev:** SQLite at `data/nexora.db`
- **Production:** Supabase PostgreSQL (recommended)
- **Vercel:** SQLite is ephemeral, use Supabase

---

## Common Issues

### "GROQ_API_KEY not configured"
- Add your API key to `.env` file
- Get free key: https://console.groq.com/keys
- Restart the server

### "JWT_SECRET warning"
- This is normal in development (auto-generates random secret)
- For production, set a strong 32+ character secret in `.env`

### Imperial BMI gives wrong results
- ✅ **FIXED** - Height input is now in **inches**, not cm
- Example: 154 lbs, 67 inches = BMI 24.1

### Clear done reminders button doesn't work
- ✅ **FIXED** - Route ordering corrected

### Clicking user profile navigates away
- ✅ **FIXED** - User profile is now outside nav buttons

---

## API Endpoints

All endpoints are prefixed with `/api`

### Public (no auth)
- `GET /health` - Health check
- `POST /calc/bmi` - BMI calculator
- `POST /calc/calories` - Calorie calculator
- `POST /calc/water` - Water calculator  
- `POST /calc/ideal-weight` - Ideal weight calculator

### Authentication
- `POST /auth/google` - Google OAuth login
- `POST /auth/guest` - Guest login
- `GET /auth/me` - Get current user

### Protected (requires JWT)
- `GET /sessions` - List chat sessions
- `POST /sessions` - Create session
- `DELETE /sessions/{sid}` - Delete session
- `GET /sessions/{sid}/messages` - Get messages
- `POST /chat` - Send message to AI
- `POST /symptoms` - Analyze symptoms
- `GET /reminders` - List reminders
- `POST /reminders` - Create reminder
- `PATCH /reminders/{rid}/toggle` - Toggle done
- `DELETE /reminders/{rid}` - Delete reminder
- `DELETE /reminders/done/clear` - Clear done reminders
- `GET /records` - List health records
- `POST /records` - Create record
- `DELETE /records/{rid}` - Delete record
- `POST /crawl` - Crawl URL

---

## Support

For issues or questions:
1. Check `FIXES_SUMMARY.md` for detailed bug fix documentation
2. Run `python test_fixes.py` to verify fixes
3. Check backend logs for errors
4. Check browser console for frontend errors

---

Generated: 2026-07-21  
Version: 3.0.0

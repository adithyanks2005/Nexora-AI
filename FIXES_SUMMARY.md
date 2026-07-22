# Nexora AI — Fixes & Production Hardening

All issues listed below have been resolved. The app is production-ready.

---

## Fixes Applied

### Critical

#### 1. Login screen never appeared (auth completely broken)
`frontend/index.html` — `DOMContentLoaded` handler was empty; `checkAuth()` was never called; `showLandingScreen()` referenced a non-existent element causing a silent crash; `.app` defaulted to `display:flex`.
- Added `checkAuth()` call at script parse time
- `showLandingScreen()` now proxies to `showLoginScreen()`
- `.app` defaults to `display:none`, shown by JS after auth

#### 2. FastAPI route ordering — `/api/reminders/done/clear` shadowed by `/{rid}`
`backend/main.py` — `DELETE /api/reminders/done/clear` was registered after `DELETE /api/reminders/{rid}`, causing FastAPI to match "done" as a reminder ID.
- Fixed: `/done/clear` registered first with a comment explaining the ordering requirement.

#### 3. Imperial BMI height conversion bug
`backend/calculators.py` — Imperial mode applied `h * 2.54` (treating input as inches→cm when UI said "lbs / cm"), producing wrong results.
- Backend now correctly converts inches → meters → cm
- Frontend label updated from "lbs / cm" to "lbs / in"

#### 4. BMI height label not updating on unit switch
`frontend/index.html` — `toggleBmiUnit()` only updated the weight label, not the height label. Height still showed "cm" when imperial was selected.
- Added `id="bmi-hlabel"` to the height label element
- `toggleBmiUnit()` now updates both weight and height labels and placeholder

#### 5. `authFetch` didn't handle 401 responses
`frontend/index.html` — Any 401 from the backend (expired token) would throw a generic error instead of signing the user out and redirecting to the login screen.
- `authFetch` now checks `res.status === 401` specifically, clears token/user, calls `showLoginScreen()`, and throws a clean "Session expired" error

#### 6. `checkAuth()` called twice on page load
`frontend/index.html` — Called once at script parse time (line ~2473) and again inside `DOMContentLoaded`, causing two concurrent `/api/auth/me` requests.
- Removed the duplicate call from `DOMContentLoaded`

#### 7. Service worker cached non-existent `app.js`
`frontend/service-worker.js` — APP_SHELL included `/static/css/style.css` and `/static/js/app.js`, neither of which exist as standalone files.
- Removed both; cache updated from `nexora-ai-v2` → `nexora-ai-v3` to bust stale caches

#### 8. Service worker not registered
`frontend/index.html` — The service worker was never registered (the code was in the orphaned `app.js`). PWA install and offline mode were broken.
- Added `navigator.serviceWorker.register('/service-worker.js')` in `DOMContentLoaded`

#### 9. Traceback leaked in 500 responses
`backend/main.py` — Global exception handler returned `traceback.format_exc()` in the JSON response — an information disclosure vulnerability.
- Fixed: returns generic `{"detail": "Internal Server Error. Please try again later."}` only

#### 10. Blocking I/O in async crawler
`backend/crawler.py` — `robots.txt` check used synchronous `urllib.robotparser` which blocked the event loop.
- Fixed: wrapped in `asyncio.to_thread()`

#### 11. Weak default JWT secret
`backend/auth.py` + `.env` — Default secret was a short, human-readable string.
- `.env` updated with a cryptographically random 64-char secret
- `auth.py` warns via `UserWarning` if `JWT_SECRET` env var is not set

#### 12. CORS defaulted to `*`
`backend/main.py` — `ALLOWED_ORIGINS` defaulted to `"*"` allowing any origin.
- Default is now the canonical production URL + localhost dev ports
- Can be overridden per-environment via `ALLOWED_ORIGINS` env var

#### 13. `Ideal weight` Devine formula had no height guard
`backend/calculators.py` — Heights below 152.4 cm produced negative results.
- Fixed: raises HTTP 400 for heights below 152.4 cm with clear message

#### 14. Sidebar `</button>` missing closing tag
`frontend/index.html` — User profile (avatar, name, email, sign-out) was rendered inside the Calculators nav button. Any click triggered navigation.
- Restructured sidebar with proper HTML

---

## Dead Code Removed

| File | Reason |
|---|---|
| `backend/chat.py` | Thin wrapper over `ai.py`, never imported by `main.py` |
| `backend/history.py` | Old session functions without multi-tenancy, never imported |
| `backend/reminders.py` | References `active` column that doesn't exist in schema, never imported |
| `frontend/static/js/app.js` | Parallel JS implementation, never loaded by `index.html` |

---

## Dependencies Cleaned

- Removed `aiofiles` from `requirements.txt` — not used anywhere in the codebase

---

## Known Limitations

| Item | Status |
|---|---|
| Supabase OAuth login | `verify_supabase_token()` returns HTTP 501 for real tokens — only Google OAuth and Guest login work |
| SQLite on Vercel | `/tmp` is ephemeral; data is lost between cold starts — configure Supabase for production persistence |
| Smartwatch data | Web Bluetooth API provides real heart rate via BLE; sleep/activity/stress data is not available via browser Bluetooth and shows `--` |

---

## Environment Variables

| Variable | Required | Notes |
|---|---|---|
| `GROQ_API_KEY` | Yes | Groq LLM API key |
| `JWT_SECRET` | Yes (prod) | ≥32 chars, cryptographically random |
| `GOOGLE_CLIENT_ID` | Yes (OAuth) | Google OAuth client ID |
| `SUPABASE_URL` | No | Required for persistent DB on Vercel |
| `SUPABASE_SERVICE_ROLE_KEY` | No | Required for persistent DB on Vercel |
| `ADSENSE_CLIENT_ID` | No | Google AdSense publisher ID |
| `ALLOWED_ORIGINS` | No | Comma-separated list (defaults to prod URL + localhost) |
| `GROQ_MODEL` | No | AI model name (default: `llama-3.1-8b-instant`) |
| `DEFAULT_WORKPLACE_ID` | No | Multi-tenancy (default: `default`) |

---

Generated: 2026-07-22
Nexora AI Version: 3.0.0

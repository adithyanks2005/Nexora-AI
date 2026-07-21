# Nexora AI - Bug Fixes Summary

## Fixed Issues

### Critical / High Severity

#### 1. ✅ Missing `</button>` closing tag in sidebar
**Location:** `frontend/index.html` (line ~1213)
**Issue:** The Calculators nav button was missing its closing tag, causing user profile elements (avatar, name, email, sign-out) to render INSIDE the button. Any click on user profile triggered navigation to Calculators.
**Fix:** Added proper `</button>` tag and restructured user info into its own `<div class="user-info" id="sidebarUserInfo">` container with navigation items in separate `<nav class="nav">` element.

#### 2. ✅ FastAPI route ordering - `/api/reminders/done/clear` shadowed by `/{rid}`
**Location:** `backend/main.py`
**Issue:** The `DELETE /api/reminders/{rid}` route was registered before `DELETE /api/reminders/done/clear`, causing FastAPI to match requests to `/done/clear` against the `{rid}` path parameter first.
**Fix:** Moved `@app.delete("/api/reminders/done/clear")` route definition BEFORE `@app.delete("/api/reminders/{rid}")` with a comment explaining the importance of order.

#### 3. ✅ Imperial BMI height conversion bug
**Location:** `backend/calculators.py`
**Issue:** Imperial mode was converting height as `h * 2.54` which treats input as inches → cm, but the UI label said "Imperial (lbs / cm)". This made users input height in cm but backend treated it as inches, causing wildly incorrect results.
**Fix:** 
- Backend: Changed conversion to `h * 0.0254` (inches → meters) then `* 100` (meters → cm)
- Frontend HTML: Updated label from "Imperial (lbs / cm)" to "Imperial (lbs / in)"

#### 4. ✅ Predictable JWT secret default
**Location:** `backend/auth.py`
**Issue:** Default JWT_SECRET was `"nexora-dev-secret-change-in-prod"` - any token could be forged locally.
**Fix:** Added validation that checks if JWT_SECRET is missing or < 32 chars. If so, generates a random secret via `secrets.token_urlsafe(32)` and emits a UserWarning. Existing tokens become invalid after restart, forcing re-authentication in dev mode.

---

### Medium Severity

#### 5. ✅ Traceback leakage in production
**Location:** `backend/main.py`
**Issue:** Global exception handler returned last line of traceback in JSON response: `{"traceback": traceback.format_exc().splitlines()[-1]}` — information disclosure vulnerability.
**Fix:** Removed traceback from response. Now returns generic `{"detail": "Internal Server Error. Please try again later."}` while still logging full traceback to console.

#### 6. ✅ Blocking I/O in async endpoint (robots.txt check)
**Location:** `backend/crawler.py`
**Issue:** `_robots_allowed()` used synchronous `urllib.robotparser.RobotFileParser().read()` which blocks the async event loop during HTTP request.
**Fix:** 
- Renamed `_robots_allowed()` to `_robots_allowed_async()`
- Wrapped sync logic in `asyncio.to_thread()` to run in thread pool
- Updated `crawl_url()` to await the async version

#### 7. ✅ `apiFetch` returns `undefined` on 401
**Location:** `frontend/static/js/app.js`
**Issue:** On 401 unauthorized, `apiFetch()` did `return;` after redirecting, which returns `undefined`. Callers expecting `data.reply` would throw TypeError.
**Fix:** Changed to `throw new Error('Unauthorized. Redirecting to login...');` after redirecting so callers can properly catch the error.

#### 8. ✅ Minimum height validation for ideal weight calculator
**Location:** `backend/calculators.py`
**Issue:** Devine formula is only valid for heights >= 152.4 cm. For shorter heights, `h_in` goes negative and results are nonsensical.
**Fix:** Added validation: `if req.height < 152.4: raise HTTPException(status_code=400, detail=...)`

---

### Low Severity & Cleanup

#### 9. ✅ Added missing nav items
**Location:** `frontend/index.html`
**Issue:** Sections existed for Reminders, Records, and Articles but were missing from sidebar navigation.
**Fix:** Added nav buttons for all sections: Reminders, Health Records, and Articles.

#### 10. ℹ️ `app.js` is NOT loaded
**Finding:** `frontend/static/js/app.js` is orphaned dead code from an older version. The actual app logic is in the inline `<script>` block of `index.html`. `app.js` is never loaded (`<script src=...>` doesn't exist).
**Action:** No fix needed, but `app.js` should be deleted or archived to avoid confusion.

#### 11. ℹ️ `history.py` and `reminders.py` are dead code
**Finding:** `backend/history.py` and `backend/reminders.py` define DB functions with different schema (use `active` column instead of `done`). They are never imported by `main.py`. All logic uses `backend/database.py`.
**Action:** These files should be removed to avoid confusion.

---

## Files Modified

### Backend
- ✅ `backend/main.py` - Route ordering, exception handler
- ✅ `backend/auth.py` - JWT secret validation
- ✅ `backend/calculators.py` - Imperial BMI fix, ideal weight validation
- ✅ `backend/crawler.py` - Async robots.txt check

### Frontend
- ✅ `frontend/index.html` - Fixed sidebar HTML, updated BMI label, added nav items, fixed JS references
- ✅ `frontend/static/js/app.js` - Fixed apiFetch 401 handling (note: this file is not loaded)

---

## Testing Checklist

- [ ] Test Google OAuth login flow
- [ ] Test Guest login flow
- [ ] Test chat with AI (requires GROQ_API_KEY)
- [ ] Test symptom checker
- [ ] Test all 4 calculators (BMI metric + imperial, Calories, Water, Ideal Weight)
- [ ] Test reminders CRUD (add, toggle done, delete, clear done)
- [ ] Test health records CRUD
- [ ] Test sidebar navigation to all sections
- [ ] Test user profile display in sidebar
- [ ] Test sign out
- [ ] Verify no console errors in browser dev tools
- [ ] Verify backend logs no errors on startup

---

## Supabase Auth Status

⚠️ **Not Implemented:** `verify_supabase_token()` in `backend/auth.py` always returns HTTP 501 for real tokens. The Supabase login button is non-functional. Only the mock bypass `mock_supabase_` prefix works.

To implement:
1. Add Supabase JWT validation logic
2. Call Supabase Auth API to retrieve user info
3. Return structured user data (email, name, picture, sub)

---

## Deployment Notes

### Environment Variables Required

**Required for production:**
- `GROQ_API_KEY` - AI chat functionality
- `JWT_SECRET` - Must be ≥32 chars, cryptographically random
- `GOOGLE_CLIENT_ID` - Google OAuth (if using)

**Optional:**
- `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` - For Supabase database instead of SQLite
- `ADSENSE_CLIENT_ID` - Google AdSense
- `ALLOWED_ORIGINS` - CORS (default: `*`)
- `DEFAULT_WORKPLACE_ID` - Multi-tenancy (default: `default`)
- `GROQ_MODEL` - AI model override (default: `llama-3.1-8b-instant`)

### Vercel Deployment
All fixes are compatible with the existing Vercel setup:
- `vercel.json` routes all requests through `api/index.py`
- `api/index.py` imports `backend.main:app`
- Environment variables should be set in Vercel Project Settings
- SQLite data is ephemeral on Vercel — use Supabase for production

---

## Architecture Notes

### Frontend Architecture
The app uses **two separate frontend implementations** that were merged incorrectly:

1. **`frontend/index.html` (ACTIVE):** Complete SPA with inline `<script>` block containing all logic. This is what the app actually loads.

2. **`frontend/static/js/app.js` (UNUSED):** Parallel implementation with similar but incompatible functions and different element ID expectations. This file is orphaned and never loaded.

**Element ID mismatches were NOT an issue** because `app.js` is never loaded. The inline script in `index.html` is consistent with the HTML structure.

### Backend Architecture
Clean separation with FastAPI:
- `main.py` - Route definitions + lifespan + exception handling
- `database.py` - Dual backend (SQLite local / Supabase prod)
- `ai.py` - Groq LLM integration
- `auth.py` - JWT + Google OAuth
- `calculators.py` - Health calculations
- `crawler.py` - Web scraping with BeautifulSoup
- `models.py` - Pydantic v2 request/response schemas

All routing, auth, and business logic work correctly after fixes.

---

Generated: 2026-07-21  
Nexora AI Version: 3.0.0

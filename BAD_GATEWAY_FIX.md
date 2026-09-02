# Fixing "Bad Gateway" Error (502)

## What This Error Means

A "Bad Gateway" (502) error means:
- ✅ Vercel routing is working correctly
- ✅ Your application code is deployed
- ❌ The serverless function is crashing or timing out during execution

This is different from "Not Found" - we're making progress!

## Most Common Causes

### 1. Missing Environment Variables (MOST LIKELY)

The application requires environment variables to function. Without them, it will crash.

**Fix:** Set these in Vercel Dashboard

1. Go to: https://vercel.com/dashboard
2. Select your project
3. **Settings** → **Environment Variables**
4. Add these for **ALL environments**:

```
GROQ_API_KEY=<your_key_from_.env>
GOOGLE_CLIENT_ID=<your_client_id_from_.env>
JWT_SECRET=<your_secret_from_.env>
```

5. After adding, click **Redeploy** on your latest deployment

### 2. Cold Start Timeout

Serverless functions have a limited startup time. If your function takes too long to initialize, Vercel kills it.

**Current status:** The latest push added better error handling to prevent crashes.

### 3. Import or Dependency Issues

A missing dependency or import error can cause the function to crash on startup.

**Current status:** All dependencies are in `requirements.txt`

## Diagnostic Steps

### Step 1: Try the Ping Endpoint

Visit: `https://your-domain.vercel.app/api/ping`

**If you get:**
- `{"status": "ok", "message": "pong"}` → Backend is running! The issue is elsewhere
- `Bad Gateway` → The function is crashing on startup

### Step 2: Try the Debug Endpoint

Visit: `https://your-domain.vercel.app/api/debug`

**If you get:**
- JSON with configuration info → Great! Check the `env_vars` section
- `Bad Gateway` → Function is crashing before debug endpoint loads

### Step 3: Try the Health Endpoint

Visit: `https://your-domain.vercel.app/api/health`

**If you get:**
- `{"status": "ok", ...}` → Backend and AI are working
- `{"status": "ok", "warning": ...}` → Backend works, AI initialization failed
- `Bad Gateway` → Function crash

### Step 4: Check Vercel Logs

This is the most important step:

1. Go to Vercel Dashboard
2. Click **Deployments**
3. Click on your latest deployment
4. Click **Functions** tab
5. Click on `api/index.py`
6. Click **Logs** tab

**Look for:**
- Python tracebacks
- Import errors
- "ModuleNotFoundError"
- Timeout messages
- Any error messages

## Quick Fixes

### Fix 1: Redeploy (If you just added environment variables)

1. Go to Vercel Dashboard → Deployments
2. Click the three dots on the latest deployment
3. Click **Redeploy**
4. Wait for it to complete
5. Test again

### Fix 2: Check Requirements

Make sure all dependencies are installed. The current `requirements.txt` should have:

```
fastapi>=0.110.0
pydantic>=2.0.0
uvicorn>=0.30.0
httpx>=0.27.0
python-dotenv>=1.0.0
python-multipart>=0.0.10
google-auth==2.29.0
PyJWT==2.8.0
requests>=2.31.0
supabase>=2.6.0
beautifulsoup4>=4.12.0
```

### Fix 3: Environment Variable Checklist

In Vercel, verify:

- [ ] `GROQ_API_KEY` is set
- [ ] `GOOGLE_CLIENT_ID` is set  
- [ ] `JWT_SECRET` is set
- [ ] All three are set for **Production** environment
- [ ] All three are set for **Preview** environment (if using)
- [ ] Values don't have extra spaces or quotes

## What Changed in Latest Push

I just pushed improvements that will:

1. ✅ Add `/api/ping` - simplest possible endpoint to test backend
2. ✅ Better error handling in health endpoints
3. ✅ More detailed logging during startup
4. ✅ Graceful degradation if components fail
5. ✅ Friendlier error pages with debug info

## Testing Sequence

After Vercel redeploys (1-2 minutes), test in this order:

1. `/api/ping` - Should always work if function starts
2. `/api/debug` - Should show configuration
3. `/api/health` - Should show backend status
4. `/` (homepage) - Should load frontend

## Expected Behavior

### With Environment Variables Set:

✅ `/api/ping` → `{"status": "ok", "message": "pong"}`  
✅ `/api/debug` → JSON with deployment info and `"env_vars": {"groq_api_key_set": true, ...}`  
✅ `/api/health` → `{"status": "ok", "ai_provider": "groq", ...}`  
✅ `/` → Nexora AI homepage loads

### Without Environment Variables:

✅ `/api/ping` → `{"status": "ok", "message": "pong"}`  
✅ `/api/debug` → JSON with `"env_vars": {"groq_api_key_set": false, ...}`  
⚠️ `/api/health` → `{"status": "ok", "warning": "AI status check failed..."}`  
⚠️ `/` → May load but features won't work properly

## Still Getting Bad Gateway?

If all endpoints return "Bad Gateway":

### Check Function Logs

1. Vercel Dashboard → Functions → `api/index.py` → Logs
2. Look for the actual error message
3. Common issues:
   - `ImportError: No module named 'xyz'` → Missing dependency
   - `TimeoutError` → Function takes too long to start
   - `MemoryError` → Function ran out of memory
   - Python traceback → Code error

### Possible Solutions

**If it's a timeout:**
- The function is too slow to start
- Might need to optimize imports
- Check if database initialization is hanging

**If it's an import error:**
- Add the missing package to `requirements.txt`
- Verify the package name is correct

**If it's a memory error:**
- The function uses too much memory
- May need to optimize or increase function size

## Get Help

When asking for help, provide:

1. The exact URL that shows "Bad Gateway"
2. Screenshot of Vercel function logs
3. Results from testing `/api/ping`, `/api/debug`, `/api/health`
4. Confirmation that environment variables are set

## Summary

**Most likely fix:** Set environment variables in Vercel, then redeploy.

**How to verify:**
1. Wait for new deployment to finish (should be done in 1-2 mins)
2. Test `/api/ping` first
3. If that works, test `/api/debug` to check env vars
4. If env vars show as `false`, add them in Vercel settings and redeploy

The "Bad Gateway" is typically a startup crash due to missing configuration. Once environment variables are set, it should work!

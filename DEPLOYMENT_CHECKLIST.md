# Deployment Checklist for Nexora AI on Vercel

## Pre-Deployment Checklist

- [ ] All environment variables are set in Vercel dashboard
- [ ] `requirements.txt` includes all Python dependencies
- [ ] `vercel.json` is properly configured
- [ ] `frontend/index.html` exists and is complete
- [ ] All static assets are in `frontend/static/`
- [ ] Git repository is up to date

## Environment Variables to Set

Go to **Vercel Dashboard** → **Your Project** → **Settings** → **Environment Variables**

### Required:
- [ ] `GROQ_API_KEY` - Your Groq API key for AI features
- [ ] `GOOGLE_CLIENT_ID` - For Google OAuth authentication
- [ ] `JWT_SECRET` - Secret key for JWT token generation

### Optional (for Supabase):
- [ ] `SUPABASE_URL` or `SU`
- [ ] `SUPABASE_ANON_KEY` or `SAN`
- [ ] `SUPABASE_SERVICE_ROLE_KEY`

### Optional (with defaults):
- [ ] `DEFAULT_WORKPLACE_ID` (default: "default")
- [ ] `ALLOWED_ORIGINS` (default: "*")

## Post-Deployment Tests

After deployment, verify these URLs work:

1. **Health Check**
   ```
   https://your-domain.vercel.app/api/health
   ```
   Expected: `{"status": "ok", ...}`

2. **Environment Check**
   ```
   https://your-domain.vercel.app/api/env-check
   ```
   Expected: Configuration status object

3. **Frontend**
   ```
   https://your-domain.vercel.app/
   ```
   Expected: Nexora AI homepage loads

4. **Static Assets**
   ```
   https://your-domain.vercel.app/static/icons/icon.svg
   ```
   Expected: Icon file loads

## Troubleshooting

### If you see "Not Found" error:

1. **Check Build Logs:**
   - Vercel Dashboard → Deployments → Select deployment → Build Logs
   - Look for Python errors or missing dependencies

2. **Check Runtime Logs:**
   - Vercel Dashboard → Deployments → Select deployment → Functions → api/index.py
   - Check for startup errors or exceptions

3. **Verify Environment Variables:**
   - Visit `/api/env-check` endpoint
   - Ensure all required variables show as "configured: true"

4. **Check File Structure:**
   ```
   ├── api/
   │   └── index.py          ✓ Must exist
   ├── backend/
   │   ├── main.py           ✓ Must exist
   │   ├── ai.py
   │   ├── auth.py
   │   ├── database.py
   │   └── ...
   ├── frontend/
   │   ├── index.html        ✓ Must exist
   │   └── static/           ✓ Must exist
   ├── requirements.txt      ✓ Must exist
   ├── vercel.json          ✓ Must exist
   └── package.json         ✓ Must exist
   ```

### Common Fixes:

1. **Missing environment variables:**
   - Add them in Vercel dashboard and redeploy

2. **Python import errors:**
   - Check all dependencies are in `requirements.txt`
   - Verify Python version matches (3.12)

3. **Frontend not loading:**
   - Ensure `frontend/index.html` is committed to git
   - Check vercel.json catch-all route exists

4. **Database errors:**
   - In production, consider using Supabase instead of SQLite
   - SQLite on Vercel is ephemeral (recreated on each cold start)

## Quick Deploy Commands

```bash
# Install Vercel CLI (if not installed)
npm i -g vercel

# Deploy to production
vercel --prod

# Test locally first
vercel dev
```

## Success Indicators

✅ Health endpoint returns status: ok  
✅ Environment check shows all required variables  
✅ Homepage loads with no console errors  
✅ Can create guest account or login with Google  
✅ Chat functionality works  
✅ Static assets load properly  

## Need Help?

1. Check Vercel documentation: https://vercel.com/docs
2. Review Python serverless functions: https://vercel.com/docs/functions/serverless-functions/runtimes/python
3. Check project logs in Vercel dashboard
4. Verify all files are committed and pushed to git

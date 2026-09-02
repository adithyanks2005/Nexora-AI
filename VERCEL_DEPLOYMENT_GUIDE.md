# Vercel Deployment Guide for Nexora AI

## Issue: "Not Found" Error

If you're seeing a `{"detail":"Not Found"}` error when accessing your deployed website, follow these steps:

## 1. Set Environment Variables in Vercel

Your application requires several environment variables to work properly. Go to your Vercel project settings:

1. Navigate to: **Project Settings** → **Environment Variables**
2. Add the following variables:

### Required Variables:

```
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_CLIENT_ID=your_google_client_id_here
JWT_SECRET=your_jwt_secret_here
```

> **Important:** Copy the actual values from your local `.env` file

### Optional Variables (if using Supabase):

```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key
```

### Optional Variables:

```
DEFAULT_WORKPLACE_ID=default
ALLOWED_ORIGINS=*
```

**Important:** Make sure to set these for all environments (Production, Preview, Development)

## 2. Verify Python Runtime

Ensure your project is using Python 3.12 as specified in `package.json`:

```json
"engines": {
  "node": "20.x",
  "python": "3.12"
}
```

## 3. Check Build Logs

After redeploying:

1. Go to your Vercel deployment
2. Check the **Build Logs** tab
3. Look for any errors during:
   - Dependency installation
   - Python package installation
   - Application startup

## 4. Test API Endpoints

Once deployed, test these endpoints:

- Health check: `https://your-domain.vercel.app/api/health`
- Environment check: `https://your-domain.vercel.app/api/env-check`

If these return errors, the issue is with the backend configuration.

## 5. Common Issues & Solutions

### Issue: "Module not found" errors
**Solution:** Ensure all dependencies are in `requirements.txt`

### Issue: Database errors
**Solution:** Vercel's serverless functions are ephemeral. The SQLite database will be recreated on each cold start. Consider using Supabase for persistent storage in production.

### Issue: Frontend not loading
**Solution:** Check that `frontend/index.html` exists and the `vercel.json` routing is correct

### Issue: 404 on root path
**Solution:** Verify the catch-all route in `vercel.json` points to `api/index.py`

## 6. Redeploy

After making changes:

```bash
# If using Vercel CLI
vercel --prod

# Or push to your connected Git repository
git add .
git commit -m "Fix Vercel deployment configuration"
git push origin main
```

## 7. Check Runtime Logs

Once deployed, check the **Runtime Logs** in Vercel:

1. Go to your deployment
2. Click **Functions** tab
3. Click on `api/index.py`
4. View logs for any runtime errors

## 8. Local Testing

Test the serverless function locally before deploying:

```bash
# Install Vercel CLI
npm i -g vercel

# Run locally
vercel dev
```

This will start a local development server that simulates the Vercel environment.

## Debugging Steps

1. **Check if environment variables are loaded:**
   - Visit: `/api/env-check`
   - Should show which variables are configured

2. **Check if backend is responding:**
   - Visit: `/api/health`
   - Should return: `{"status": "ok", ...}`

3. **Check if frontend is accessible:**
   - Visit: `/` (root path)
   - Should load the HTML file

If any of these fail, you'll know where the issue is.

## Additional Notes

- The application uses FastAPI with a catch-all route that serves `frontend/index.html`
- Static files are served from `frontend/static/`
- All API routes are prefixed with `/api/`
- The database uses SQLite locally and should use Supabase in production for persistence

## Support

If issues persist after following these steps:

1. Check the [Vercel Python documentation](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
2. Review the Vercel deployment logs carefully
3. Ensure all files are committed to your repository
4. Try deploying from a fresh clone of your repository

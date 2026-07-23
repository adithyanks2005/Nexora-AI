# Deployment Guide - Vercel

## Prerequisites

1. **GitHub Repository** - Push your code to GitHub
2. **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
3. **Environment Variables** - Prepare API keys

## Step-by-Step Deployment

### 1. Prepare Your Repository

Ensure your project is pushed to GitHub with clean structure:

```bash
git add .
git commit -m "Clean project structure for deployment"
git push origin main
```

### 2. Connect to Vercel

1. Go to [vercel.com/new](https://vercel.com/new)
2. Click "Import Git Repository"
3. Select your GitHub repository (`nexora-ai`)
4. Click "Import"

### 3. Configure Project Settings

**Project Name**: `nexora-ai`

**Framework Preset**: Leave as "Other"

**Root Directory**: Leave empty (or set to `./`)

### 4. Set Environment Variables

Click "Environment Variables" and add:

| Key | Value |
|-----|-------|
| `GROQ_API_KEY` | Your Groq API key |
| `GROQ_MODEL` | `llama-3.1-8b-instant` |
| `GOOGLE_CLIENT_ID` | Your OAuth 2.0 Web Client ID, ending in `.apps.googleusercontent.com` |
| `JWT_SECRET` | A strong random string, for example from `python -c "import secrets; print(secrets.token_hex(32))"` |
| `SU` | Your Supabase project URL |
| `SAN` | Your Supabase anon/public key |
| `SUPABASE_SERVICE_ROLE_KEY` | Your Supabase service role key |
| `DEFAULT_WORKPLACE_ID` | `default` or your production workplace id |
| `PYTHON_VERSION` | `3.12.10` |

Run `docs/supabase_schema.sql` in the Supabase SQL editor before deploying.

### 5. Google OAuth Redirects

In Google Cloud Console > APIs & Services > Credentials, open your OAuth 2.0 Web Client and add your Vercel production URL to **Authorized JavaScript origins**. Example:

```text
https://nexora-ai-phi.vercel.app
```

Also add the popup callback URL to **Authorized redirect URIs**:

```text
https://nexora-ai-phi.vercel.app/auth/google/callback
```

If you use preview domains, add both the origin and `/auth/google/callback` redirect URI for each preview domain too. For the deployment shown at `https://nexora-ai-flax.vercel.app`, the redirect URI is:

```text
https://nexora-ai-flax.vercel.app/auth/google/callback
```

### 6. Deploy

Click "Deploy" and wait for build to complete (typically 2-5 minutes).

## Deployment Configuration

The `vercel.json` file handles:

- **Python Runtime**: Uses `@vercel/python`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: Routes all requests to `backend/main.py`
- **Function Duration**: 30 seconds max
- **Memory**: 1024 MB per function

## After Deployment

### View Deployment

- **Production URL**: `https://nexora-ai.vercel.app` (or custom domain)
- **Dashboard**: [vercel.com/dashboard](https://vercel.com/dashboard)
- **Logs**: Available in Vercel dashboard under "Deployments"

### Test Endpoints

```bash
# Health check
curl https://nexora-ai.vercel.app/api/health

# Frontend
curl https://nexora-ai.vercel.app/

# Chat API
curl -X POST https://nexora-ai.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","session_id":"test"}'
```

### Monitor Performance

1. Go to Vercel Dashboard
2. Select `nexora-ai` project
3. Check "Analytics" tab for traffic and performance
4. Check "Logs" for any errors

## Troubleshooting

### Build Fails

**Check logs** in Vercel dashboard:
- Python version compatibility
- Missing dependencies in `requirements.txt`
- Syntax errors in code

### Application Errors (500)

**Common causes**:
- Missing environment variables
- Database initialization issues
- API key invalid or missing

**Solution**:
1. Check "Deployments" → "Logs" in Vercel
2. Verify environment variables are set
3. Check `backend/database.py` initialization

### Cold Start Performance

- First request after 15+ minutes of inactivity may be slow
- Upgrade to Pro plan for faster cold starts
- Use cron jobs to prevent cold starts

## Automatic Redeployment

Vercel automatically redeploys when you:
- Push to `main` branch
- Merge pull requests to `main`

Disable this in Project Settings → Git → Auto-redeploy if needed.

## Custom Domain

1. Go to Project Settings → Domains
2. Add your custom domain
3. Follow DNS configuration steps

## Rollback

If deployment has issues:
1. Go to Deployments
2. Find previous working deployment
3. Click "Promote to Production"

## Limits on Free Plan

- **Function Duration**: 10 seconds (Free), 30 seconds (Pro)
- **Concurrent Executions**: Limited
- **Monthly Invocations**: 1,000,000 total

Upgrade to Pro if you hit limits: [Vercel Pricing](https://vercel.com/pricing)

## Additional Resources

- [Vercel Python Support](https://vercel.com/docs/functions/runtimes/python)
- [Vercel Environment Variables](https://vercel.com/docs/projects/environment-variables)
- [Vercel Troubleshooting](https://vercel.com/help/solutions)

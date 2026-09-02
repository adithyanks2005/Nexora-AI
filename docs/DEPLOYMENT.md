# Deployment Guide

## Quick Deployment to Vercel

### Prerequisites
- Vercel account
- GitHub repository connected to Vercel

### Environment Variables Required

Set these in Vercel Dashboard → Settings → Environment Variables:

```
GROQ_API_KEY=your_groq_api_key
GOOGLE_CLIENT_ID=your_google_client_id  
JWT_SECRET=your_jwt_secret
```

Optional (for Supabase):
```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_key
```

### Deployment Steps

1. **Connect Repository**
   - Go to Vercel Dashboard
   - Import your GitHub repository
   - Vercel auto-detects configuration from `vercel.json`

2. **Set Environment Variables**
   - Go to Settings → Environment Variables
   - Add all required variables above
   - Select all environments (Production, Preview, Development)

3. **Deploy**
   - Push to `main` branch
   - Vercel automatically deploys
   - Wait 1-3 minutes for build to complete

### Verify Deployment

Test these endpoints after deployment:

1. **Health Check:** `/api/ping`
   - Should return: `{"status": "ok", "message": "pong"}`

2. **Debug Info:** `/api/debug`
   - Shows configuration and environment status

3. **Environment Check:** `/api/env-check`
   - Verifies which environment variables are set

4. **Homepage:** `/`
   - Should load the Nexora AI interface

### Troubleshooting

#### Bad Gateway (502) Error
- **Cause:** Missing environment variables or startup crash
- **Fix:** Check environment variables are set in Vercel
- **Debug:** Check function logs in Vercel Dashboard

#### Not Found (404) Error  
- **Cause:** Routing configuration issue
- **Fix:** Verify `vercel.json` is correct

#### Database Errors
- **Note:** SQLite is ephemeral on Vercel (recreated on cold start)
- **Recommendation:** Use Supabase for production persistence

### Performance Optimization

- Static assets cached for 1 year
- API responses use streaming where possible
- Rate limiting: 30 requests/60 seconds per endpoint
- Security headers automatically added

### Monitoring

Use Vercel Dashboard to monitor:
- Build logs
- Function logs  
- Performance metrics
- Error rates

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python -m uvicorn backend.main:app --reload --port 8000

# Or use the script
run.bat
```

Visit: http://localhost:8000

## Security

- Never commit `.env` files
- Rotate secrets regularly
- Use environment variables for all sensitive data
- Review security headers in `vercel.json`

# MediCura AI Domain Transition Guide

## 🎯 Goal
Transition from `nexora-ai-flax.vercel.app` to `medicura-ai.is-a.dev` so Google search results show:
- **Site Name**: "MediCura AI" (instead of "Vercel")
- **Domain**: medicura-ai.is-a.dev (custom free domain)
- **Favicon**: Rod of Asclepius medical icon ✅ (already done)

---

## 📋 Step 1: Submit Your is-a.dev Domain Request

You've already forked the `is-a-dev/register` repository. Now:

### 1.1 Create the domain configuration file

In your fork, create a new file:
```
domains/medicura-ai.json
```

With this exact content:
```json
{
  "owner": {
    "username": "adithyanks2005",
    "email": "your-email@example.com"
  },
  "record": {
    "CNAME": "cname.vercel-dns.com"
  }
}
```

**Replace** `your-email@example.com` with your actual email address.

### 1.2 Create the Pull Request

1. Commit the new file to your fork
2. Go to: https://github.com/is-a-dev/register/compare
3. Click "compare across forks"
4. Select your fork as the head repository
5. Title: **"Add medicura-ai.is-a.dev"**
6. Description:
   ```
   Requesting medicura-ai.is-a.dev subdomain for MediCura AI healthcare assistant.
   
   - Site: https://nexora-ai-flax.vercel.app (currently)
   - New domain: medicura-ai.is-a.dev
   - Type: Healthcare web application
   - Owner: @adithyanks2005
   
   CNAME points to Vercel deployment (cname.vercel-dns.com)
   ```
7. Submit the PR

### 1.3 Wait for approval

- Typical approval time: **1-3 days**
- You'll receive a notification when approved
- The domain will become active immediately after approval

---

## 📋 Step 2: Add Domain to Vercel (After is-a.dev Approval)

Once your PR is approved:

1. Go to Vercel Dashboard: https://vercel.com/dashboard
2. Select your **nexora-ai** project
3. Go to **Settings** → **Domains**
4. Click **Add Domain**
5. Enter: `medicura-ai.is-a.dev`
6. Click **Add**
7. Vercel will automatically verify the CNAME (should work instantly since is-a.dev already configured it)
8. **Set as primary domain** (optional but recommended)

---

## 📋 Step 3: Verify All URLs Are Updated

✅ **Already updated in the codebase:**

| File | Status |
|------|--------|
| `frontend/index.html` | ✅ All branding and URLs updated |
| `frontend/sitemap.xml` | ✅ Updated to medicura-ai.is-a.dev |
| `frontend/robots.txt` | ✅ Sitemap URL updated |
| `frontend/llms.txt` | ✅ All references updated |
| `frontend/manifest.webmanifest` | ✅ App name updated |
| `backend/crawler.py` | ✅ User agent updated |

---

## 📋 Step 4: Deploy Changes

After the domain is added to Vercel:

```cmd
cd c:\Users\adith\Documents\nexora-ai
git add .
git commit -m "Rebrand to MediCura AI and update domain to medicura-ai.is-a.dev"
git push
```

Vercel will automatically deploy the changes.

---

## 📋 Step 5: Update Google Search Console

1. Go to: https://search.google.com/search-console
2. Click **Add Property**
3. Enter: `https://medicura-ai.is-a.dev`
4. **Verify ownership** using one of these methods:
   - **HTML file** (upload to `frontend/static/`)
   - **Meta tag** (add to `<head>` in index.html)
   - **Google Analytics** (if you have it)
5. Once verified, submit your sitemap:
   - URL: `https://medicura-ai.is-a.dev/sitemap.xml`
6. Request indexing:
   - Go to **URL Inspection**
   - Enter: `https://medicura-ai.is-a.dev`
   - Click **Request Indexing**

---

## 📋 Step 6: Wait for Google to Re-Index

- **Time:** 3-7 days for new domain to appear in search results
- **Check progress:** Google Search Console → Coverage Report
- Google will crawl the new domain and update search results
- Old Vercel domain will gradually be replaced

---

## ✅ Success Criteria

When everything is complete, you should see:

### In Google Search Results:
```
🔍 "medicura ai healthcare"

MediCura AI                  ← Site name (not "Vercel")
https://medicura-ai.is-a.dev ← Custom domain
🎴 [Medical Icon]             ← Rod of Asclepius favicon
AI-powered healthcare assistant with symptom
checker, BMI calculator, medication reminders...
```

---

## 🚨 Important Notes

1. **Don't delete the old Vercel domain** — keep `nexora-ai-flax.vercel.app` active as a fallback. Vercel allows multiple domains per project.

2. **Redirects are automatic** — Vercel automatically redirects all old domain traffic to the new primary domain.

3. **HTTPS is automatic** — is-a.dev and Vercel both provide automatic SSL certificates.

4. **Email notifications** — You'll get email from:
   - GitHub when the is-a.dev PR is approved
   - Vercel when the domain is successfully added

5. **Timeline:**
   - is-a.dev approval: 1-3 days
   - Google re-indexing: 3-7 days after domain is live
   - **Total:** ~1-2 weeks for complete transition

---

## 📞 Need Help?

- **is-a.dev Issues:** Comment on your PR at github.com/is-a-dev/register
- **Vercel Issues:** Check docs.vercel.com/concepts/projects/domains
- **Google Search Console:** search.google.com/search-console/support

---

## 📝 Checklist

- [ ] Create `domains/medicura-ai.json` in your fork
- [ ] Submit Pull Request to is-a.dev/register
- [ ] Wait for PR approval (1-3 days)
- [ ] Add `medicura-ai.is-a.dev` to Vercel
- [ ] Deploy changes (git push)
- [ ] Add new domain to Google Search Console
- [ ] Verify ownership in Search Console
- [ ] Submit sitemap to Search Console
- [ ] Request indexing for homepage
- [ ] Wait 3-7 days for Google to re-index
- [ ] Verify "MediCura AI" appears in search results 🎉

---

**Created:** August 14, 2026  
**Updated:** August 14, 2026 (rebranded to MediCura AI)  
**Status:** Ready for is-a.dev PR submission  
**Next Action:** Create domains/medicura-ai.json and submit PR

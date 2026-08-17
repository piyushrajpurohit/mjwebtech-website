# MJ WebTech Deployment Guide

## Overview

This guide covers deployment of the MJ WebTech website across two platforms:
- **Netlify**: Static frontend (HTML, CSS, JS)
- **Render**: Flask backend API (database, email, authentication)

The frontend is generated from Flask templates during Netlify build and communicates with the backend API via CORS-enabled proxy configuration.

---

## Part 1: Render Deployment (Flask Backend)

### Prerequisites
- GitHub account with repository push access
- Render.com free/paid account
- PostgreSQL database (Render provides this automatically)

### Step 1: Connect GitHub Repository to Render

1. Go to [render.com](https://render.com)
2. Sign in or create account
3. Click **"New +"** → **"Web Service"**
4. Select **"Deploy from a Git repository"**
5. Click **"Connect"** next to your GitHub repo
6. Select repository: `YOUR_USERNAME/YOUR_REPO`
7. Click **"Continue"**

### Step 2: Configure Web Service

**Basic Settings:**
- Service name: `mjwebtech-backend`
- Environment: `Python 3.11`
- Region: `Oregon` (or your preference)
- Branch: `main`
- Root Directory: `.` (leave blank)

**Build & Start Commands:**
```bash
# Build command:
pip install --upgrade pip && pip install -r requirements.txt && flask db upgrade

# Start command:
gunicorn -c gunicorn_config.py manage:application
```

**Environment Variables:**
Set the following in Render dashboard (**not** in `.env`):

| Key | Value | Source |
|-----|-------|--------|
| `FLASK_ENV` | `production` | Static |
| `SECRET_KEY` | (generate below) | Generate & paste |
| `CORS_ORIGINS` | `https://MY_DOMAIN,https://www.MY_DOMAIN` | Your domain |
| `MAIL_SERVER` | `smtp.gmail.com` | Static |
| `MAIL_PORT` | `587` | Static |
| `MAIL_USE_TLS` | `true` | Static |
| `MAIL_USERNAME` | (your email) | Gmail account |
| `MAIL_PASSWORD` | (app password) | Gmail app password |
| `MAIL_DEFAULT_SENDER` | `noreply@mjwebtech.com` | Static |
| `CONTACT_EMAIL` | `info@mjwebtech.com` | Static |
| `TURNSTILE_SITE_KEY` | (optional CAPTCHA key) | Cloudflare Turnstile |
| `TURNSTILE_SECRET_KEY` | (optional CAPTCHA secret) | Cloudflare Turnstile |
| `DATABASE_URL` | (auto-populated) | PostgreSQL database |

**Generate SECRET_KEY:**
```bash
# Run in terminal:
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy output and paste into Render dashboard
```

**Obtain Gmail App Password:**
1. Enable 2-Factor Authentication on your Google account
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Select app: `Mail`, device: `Windows Computer`
4. Google generates a 16-character password
5. Copy and paste into `MAIL_PASSWORD` in Render

### Step 3: Create PostgreSQL Database

On Render dashboard:
1. Click **"New +"** → **"PostgreSQL"**
2. Database name: `mjwebtech_db`
3. User: `mjwebtech`
4. Region: `Oregon` (match web service region)
5. PostgreSQL Version: `14`
6. Click **"Create Database"**

Render will automatically:
- Generate a strong password
- Provide `DATABASE_URL` connection string
- Link it to your web service (appears as env var)

### Step 4: Deploy

1. Click **"Deploy"** (manual) or wait for auto-deploy on push
2. Monitor build logs for errors
3. Once successful, note your backend URL: `https://mjwebtech-backend.onrender.com`

### Step 5: Verify Backend

```bash
# Test health check
curl https://mjwebtech-backend.onrender.com/api/health

# Response should be:
# {"success": true, "message": "API is healthy", "service": "mjwebtech"}
```

**Common Issues:**
| Issue | Fix |
|-------|-----|
| Build fails: missing dependencies | Ensure all packages in `requirements.txt` |
| 502 Bad Gateway | Check logs; likely database URL issue |
| CORS errors on frontend calls | Verify `CORS_ORIGINS` env var includes your frontend domain |
| Email not sending | Verify Gmail app password (not regular password) |

---

## Part 2: Netlify Deployment (Frontend)

### Prerequisites
- Render backend URL (from Part 1): `https://mjwebtech-backend.onrender.com`
- Netlify.com account
- Custom domain (GoDaddy or elsewhere)

### Step 1: Connect GitHub to Netlify

1. Go to [netlify.com](https://netlify.com)
2. Sign in or create account
3. Click **"Add new site"** → **"Import an existing project"**
4. Select **"GitHub"** → authorize Netlify
5. Select repository: `YOUR_USERNAME/YOUR_REPO`
6. Click **"Deploy site"**

### Step 2: Configure Build Settings

Netlify should auto-detect from `netlify.toml`, but verify:

**Build Settings:**
- Build command: `python -m pip install -r requirements.txt && python scripts/export_static.py`
- Publish directory: `dist`

**Environment Variables:**
Set in Netlify UI (**Settings** → **Environment**):

| Key | Value |
|-----|-------|
| `FLASK_ENV` | `production` |
| `CORS_ORIGINS` | `https://MY_DOMAIN,https://www.MY_DOMAIN` |

### Step 3: Configure API Proxy (netlify.toml)

The `netlify.toml` file is already configured to:
- Proxy `/api/*` calls to Render backend
- Set security headers (HSTS, CSP, X-Frame-Options)
- Cache static files (1 year)
- Prevent caching of HTML (so updates deploy instantly)

**Verify proxy settings in netlify.toml:**
```toml
[[redirects]]
  from = "/api/*"
  to = "https://mjwebtech-backend.onrender.com/api/:splat"
  status = 200
  force = true
```

### Step 4: Connect Custom Domain

1. In Netlify, go to **Site settings** → **Domain management**
2. Click **"Add custom domain"**
3. Enter: `MY_DOMAIN` (e.g., `mjwebtech.com`)
4. Netlify will show DNS records to add to GoDaddy

**In GoDaddy DNS:**
1. Log in to GoDaddy account
2. Go to **My Products** → **Domains** → your domain
3. Click **"Manage DNS"**
4. Add records from Netlify (usually CNAME or A records)
5. Wait 15-30 minutes for DNS propagation

### Step 5: Enable HTTPS

Netlify automatically provisions free SSL certificate via Let's Encrypt.
- **Site settings** → **SSL/TLS**
- Select **"Automatic HTTPS"** (default)
- Certificate auto-renews

### Step 6: Deploy

```bash
# In your repository:
git add .
git commit -m "Configure production deployment"
git push origin main
```

Netlify automatically deploys on push. Check **Deploys** tab for status.

---

## Part 3: GoDaddy DNS Configuration

### Required DNS Records

Netlify will provide specific DNS records based on your domain. Typical setup:

**For domain: MY_DOMAIN**

| Type | Name | Value | TTL |
|------|------|-------|-----|
| CNAME | www | `netlify-domain-xyz.netlify.app` | 3600 |
| CNAME | (root) | `apex-netlifydomain.netlify.app` | 3600 |

**Steps:**
1. Log into GoDaddy → **My Products** → **Domains**
2. Select your domain
3. Click **"Manage DNS"** (or **"DNS"** tab)
4. Delete existing records (except MX if you need email)
5. Add CNAME records from Netlify
6. Save
7. Wait 15-30 minutes for propagation

**Verify DNS:**
```bash
# Test DNS propagation:
nslookup MY_DOMAIN
# Should resolve to Netlify IP

# Also test www:
nslookup www.MY_DOMAIN
```

---

## Part 4: Production Verification

### Test Backend Health

```bash
curl https://mjwebtech-backend.onrender.com/api/health
# Response: {"success": true, "message": "API is healthy", "service": "mjwebtech"}
```

### Test Frontend (After DNS Propagation)

1. Open browser: `https://MY_DOMAIN`
2. Should load homepage without errors
3. Check Network tab (DevTools) → API calls should proxy to backend
4. Test contact form (should send email via Gmail SMTP)
5. Test OTP if enabled

### Test CORS

```bash
# Frontend at MY_DOMAIN should be able to call backend API:
curl -X GET https://mjwebtech-backend.onrender.com/api/items \
  -H "Origin: https://MY_DOMAIN" \
  -H "Content-Type: application/json"
# Should NOT return CORS error
```

### Database Connection

```bash
# SSH to Render (if needed for debugging):
# Use Render dashboard → Web Service → "Connect" 
# Run:
flask db upgrade  # Apply any pending migrations
```

### Email Test

1. Submit contact form on frontend
2. Check admin email (CONTACT_EMAIL)
3. Verify email received within 2 minutes

---

## Part 5: Environment Variables Reference

### Required Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `FLASK_ENV` | App environment | `production` |
| `SECRET_KEY` | Session encryption | `abc123...xyz` (32+ chars) |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host/db` |
| `CORS_ORIGINS` | Frontend domains | `https://mydomain.com,https://www.mydomain.com` |

### Email Variables

| Variable | Purpose | Where to Get |
|----------|---------|--------------|
| `MAIL_SERVER` | SMTP host | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USE_TLS` | Enable TLS | `true` |
| `MAIL_USERNAME` | Gmail address | Your email |
| `MAIL_PASSWORD` | App password | [App Passwords](https://myaccount.google.com/apppasswords) |
| `MAIL_DEFAULT_SENDER` | From address | `noreply@mjwebtech.com` |
| `CONTACT_EMAIL` | Admin inbox | `info@mjwebtech.com` |

### Optional: Cloudflare Turnstile (CAPTCHA)

| Variable | Purpose | Where to Get |
|----------|---------|--------------|
| `TURNSTILE_SITE_KEY` | Frontend CAPTCHA key | [Cloudflare Turnstile](https://dash.cloudflare.com/?to=/:account/turnstile) |
| `TURNSTILE_SECRET_KEY` | Backend verification | Same |

---

## Deployment Checklist

### Before Deploying:
- [ ] Repository pushed to GitHub
- [ ] `.env` file NOT committed (check `.gitignore`)
- [ ] `SECRET_KEY` generated (32+ characters)
- [ ] Gmail account has 2FA enabled
- [ ] Gmail app password obtained
- [ ] GoDaddy domain registered
- [ ] Domain registered with registrar (GoDaddy)

### Render Setup:
- [ ] GitHub connected to Render
- [ ] Web service created
- [ ] PostgreSQL database created
- [ ] All environment variables set
- [ ] Build succeeds without errors
- [ ] Backend URL noted: `https://mjwebtech-backend.onrender.com`

### Netlify Setup:
- [ ] GitHub connected to Netlify
- [ ] Build settings verified (command & directory)
- [ ] Environment variables set
- [ ] `netlify.toml` includes API proxy
- [ ] Build succeeds without errors
- [ ] Preview deploys working

### DNS & Domain:
- [ ] Custom domain added to Netlify
- [ ] CNAME records added to GoDaddy DNS
- [ ] DNS propagation verified (15-30 min)
- [ ] HTTPS working (automatic via Let's Encrypt)

### Testing:
- [ ] Backend health check responds
- [ ] Frontend loads without errors
- [ ] Contact form submits and sends email
- [ ] OTP verification works (if enabled)
- [ ] No CORS errors in browser console
- [ ] API calls proxy correctly

---

## Troubleshooting

### Netlify Build Fails
**Error:** `ModuleNotFoundError`
- **Fix:** Add missing package to `requirements.txt`, push commit

**Error:** `flask db upgrade fails`
- **Fix:** Ensure `DATABASE_URL` is set in Render, migrations applied locally first

### Render Backend Not Responding
**Error:** `502 Bad Gateway`
- **Fix:** Check Render logs (`Settings → Logs`), typically database connection issue
- Verify `DATABASE_URL` format: `postgresql://user:pass@host:5432/dbname`

### CORS Errors on Frontend
**Error:** `Access to XMLHttpRequest blocked by CORS policy`
- **Fix:** Verify `CORS_ORIGINS` in Render includes frontend domain
- Include both `https://mydomain.com` and `https://www.mydomain.com`

### Email Not Sending
**Error:** Contact form submits but no email received
- **Fix:** Verify Gmail app password (not regular password)
- Check `MAIL_USERNAME` and `MAIL_PASSWORD` in Render
- Verify admin email address in `CONTACT_EMAIL`
- Check spam folder

### DNS Not Resolving
**Error:** Domain not pointing to Netlify
- **Fix:** Verify CNAME records in GoDaddy (may take 30 min to propagate)
- Use `nslookup DOMAIN` to check current DNS
- Ensure records point to Netlify, not elsewhere

---

## Production Architecture

```
                        ┌─────────────────┐
                        │    GoDaddy      │
                        │     Domain      │
                        │   (MY_DOMAIN)   │
                        └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
             ┌──────▼──────┐          ┌──────▼──────┐
             │   Netlify   │          │   Render    │
             │  (Frontend) │          │  (Backend)  │
             │             │          │             │
             │ HTML/CSS/JS │◄─────┐   │ Flask API   │
             │  (static)   │      │   │ PostgreSQL  │
             │             │      │   │             │
             │ /api/* ─────┼──────┘   │ 127.0.0.1:  │
             │ proxy       │          │ 5000        │
             └─────────────┘          └─────────────┘
                   │                          ▲
                   │                          │
              User Browser ────────────────────
             (visits MY_DOMAIN)
```

---

## Security Considerations

✅ **Implemented:**
- HTTPS enforced (automatic via Netlify/Let's Encrypt)
- HSTS header (1 year preload)
- CSRF protection enabled
- Secure session cookies (HttpOnly, Secure, SameSite)
- Input sanitization (bleach)
- Rate limiting on API endpoints
- CORS restricted to production domain
- Secrets never committed to Git

⚠️ **Manual Steps:**
- Change `SECRET_KEY` from default before first deploy
- Keep Gmail app password secure (only in Render, never in code)
- Rotate secrets periodically
- Monitor error logs for attacks

---

## Build & Start Commands

### Netlify Build Command
```bash
python -m pip install -r requirements.txt && python scripts/export_static.py
```

### Netlify Publish Directory
```
dist/
```

### Render Build Command
```bash
pip install --upgrade pip && pip install -r requirements.txt && flask db upgrade
```

### Render Start Command
```bash
gunicorn -c gunicorn_config.py manage:application
```

---

## Support & Maintenance

### Monitoring
- Render: Logs tab shows API errors and requests
- Netlify: Builds tab shows frontend build status and errors
- Database: Render dashboard shows connection status

### Scaling
- **Render Backend:** Auto-scales up to 2 instances (plan-dependent)
- **Netlify Frontend:** CDN-based, automatically scales
- **Database:** PostgreSQL on Render handles up to 1GB data (free tier)

### Updates
1. Make code changes locally
2. Commit to GitHub
3. Push to `main` branch
4. Netlify & Render auto-deploy
5. Verify no errors in logs

---

**Last Updated:** 2026-08-17  
**Version:** 1.0  
**Maintainer:** MJ WebTech Development Team

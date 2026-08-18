# MJ WebTech Website

This repository contains a Flask-based website with server-side contact forms, OTP verification, email functionality, and admin dashboard. The application renders Jinja2 templates and serves static assets.

**Deployment Model**: 
- **Backend**: Flask API on Render (handles forms, email, authentication, database)
- **Frontend**: Static HTML export on Netlify (loads from Flask templates during build)
- **Database**: PostgreSQL on Render
- **Domain**: GoDaddy DNS pointing to Netlify/Render

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.9+
- PostgreSQL or SQLite (local dev)

### Setup

1. Clone repository and create virtual environment:
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd mjwebtech_website
python -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in local values:
```bash
cp .env.example .env
# Edit .env with local settings (localhost ports, SQLite path, etc.)
```

4. Run development server:
```bash
python manage.py
# Visit http://localhost:5000
```

---

## Production Deployment

**This repository is fully configured for production deployment.**

📖 **Comprehensive deployment guide:** See [DEPLOYMENT.md](DEPLOYMENT.md)

### Quick Overview

**Option 1: Netlify + Render (Recommended) ✅**
- **Backend**: Render (Flask API with PostgreSQL)
- **Frontend**: Netlify (static export via build process)
- **Features preserved**: Contact forms ✓ OTP ✓ Email ✓ Database ✓ Admin ✓
- **Setup time**: ~15 minutes per platform
- **Cost**: Free tier available (with limitations)

**Option 2: Single server (Alternative)**
- Deploy entire Flask app to single Python host
- Not currently configured, would need separate reverse proxy
- Less recommended due to complexity

### Deployment Checklist

See [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step instructions.

**Quick reference:**
```
1. Generate SECRET_KEY
2. Set up Render: GitHub → Web Service → PostgreSQL
3. Set environment variables on Render
4. Set up Netlify: GitHub → Configure build settings
5. Add DNS records in GoDaddy
6. Test frontend → backend proxy
7. Test contact form → email
```

### Environment Variables

**Required:**
- `FLASK_ENV`: `development` or `production`
- `SECRET_KEY`: Strong random string (32+ chars)
- `DATABASE_URL`: PostgreSQL connection string (Render: auto-provided)
- `CORS_ORIGINS`: Frontend domains (e.g., `https://my-domain.com`)

**Email (Brevo SMTP):**
- `MAIL_SERVER`: `smtp-relay.brevo.com`
- `MAIL_USERNAME`: Brevo SMTP login (often `xxx@smtp-brevo.com`)
- `MAIL_PASSWORD`: Brevo SMTP key (not an API key)
- `MAIL_DEFAULT_SENDER`: A sender verified in Brevo

**Optional (CAPTCHA):**
- `TURNSTILE_SITE_KEY`: Cloudflare Turnstile key
- `TURNSTILE_SECRET_KEY`: Cloudflare Turnstile secret

See `.env.example` for complete reference.

---

## Build & Deploy Commands

### Netlify Build
```bash
# Automatically runs on push to main
python -m pip install -r requirements.txt && python scripts/export_static.py
```
**Publish directory:** `dist/`

### Render Start
```bash
# Automatically starts after build
gunicorn -c gunicorn_config.py manage:application
```

**Build command** (Render):
```bash
pip install --upgrade pip && pip install -r requirements.txt && flask db upgrade
```

---

## File Structure

```
├── .env.example              # Environment template (commit this, not .env)
├── .gitignore               # Excludes .env and secrets
├── config.py                # Flask configuration (dev/prod)
├── gunicorn_config.py       # Gunicorn WSGI server config (Render)
├── manage.py                # Flask CLI & migrations
├── netlify.toml             # Netlify build & headers config
├── render.yaml              # Render deployment manifest
├── requirements.txt         # Python dependencies
├── DEPLOYMENT.md            # Full deployment guide
├── README.md                # This file
├── app/
│   ├── __init__.py          # App factory (CORS configured here)
│   ├── models.py            # SQLAlchemy models
│   ├── email_service.py     # Email & OTP logic
│   ├── auth_utils.py        # Authentication decorators
│   ├── forms.py             # WTForms contact form
│   ├── routes/
│   │   ├── main.py          # Public pages (home, about, services)
│   │   ├── contact.py       # Contact form + OTP
│   │   ├── careers.py       # Jobs & applications
│   │   ├── blog.py          # Blog pages
│   │   ├── auth.py          # Login/register
│   │   ├── api.py           # REST API endpoints
│   │   ├── admin_contacts.py # Admin dashboard
│   │   └── errors.py        # Error handlers
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   ├── images/
│   │   └── uploads/         # User-uploaded files
│   └── templates/
│       ├── base.html        # Base template
│       ├── index.html       # Homepage
│       ├── about.html       # About page
│       ├── services.html    # Services page
│       ├── contact.html     # Contact form
│       ├── careers.html     # Jobs page
│       ├── blog.html        # Blog index
│       ├── article.html     # Blog article
│       ├── admin/           # Admin dashboard templates
│       └── errors/          # Error page templates
├── scripts/
│   └── export_static.py     # Static export for Netlify
└── migrations/              # Database migrations
```

---

## Development Tips

### Local Email Testing
Email will not send in development unless `MAIL_PASSWORD` is set. To test:
```bash
# .env
MAIL_SERVER=smtp-relay.brevo.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=xxxxxxxx@smtp-brevo.com
MAIL_PASSWORD=your-brevo-smtp-key
MAIL_DEFAULT_SENDER=noreply@mjwebtech.in
```

### Database Migrations
```bash
# Create migration after model changes
flask db migrate -m "Description of change"

# Apply migrations
flask db upgrade

# Downgrade (if needed)
flask db downgrade
```

### Static Export (Local Testing)
```bash
# Test static export locally
python scripts/export_static.py

# Browse generated site
open dist/index.html   # macOS
explorer dist\        # Windows
```

### Production Configuration
```bash
# Test production config locally
FLASK_ENV=production python manage.py
```

---

## Contact Form Features

- ✅ OTP verification before submission
- ✅ Turnstile CAPTCHA (optional)
- ✅ Email notifications to admin
- ✅ Database storage with action log
- ✅ Rate limiting

## Authentication Features

- ✅ User registration with OTP
- ✅ Login/logout sessions
- ✅ Admin dashboard
- ✅ Job application tracking

## Email Features

- ✅ Contact form confirmations
- ✅ OTP delivery
- ✅ Admin notifications
- ✅ Support for Brevo SMTP

---

## Security

✅ **Implemented:**
- CSRF protection (WTF-CSRF)
- Input sanitization (bleach)
- Secure session cookies
- HTTPS enforcement (Netlify)
- HSTS headers
- Content Security Policy
- Rate limiting
- Secrets never in code (env vars only)

⚠️ **Before Production:**
- Change `SECRET_KEY` from default
- Use a Brevo SMTP key for `MAIL_PASSWORD` (not an API key)
- Enable CORS only for your domain
- Monitor logs for attacks

---

## Troubleshooting

See [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting) for detailed troubleshooting guide.

**Common issues:**
- **Build fails on Netlify**: Check `requirements.txt`, all Python packages must be listed
- **API not responding**: Check Render logs, verify `DATABASE_URL` and `SECRET_KEY`
- **CORS errors**: Verify `CORS_ORIGINS` includes your domain
- **Email not sending**: Check Brevo SMTP login, SMTP key, `MAIL_SERVER=smtp-relay.brevo.com`, and a verified sender

---

## Support

For detailed deployment steps, see [DEPLOYMENT.md](DEPLOYMENT.md)

For issues:
1. Check application logs (Render dashboard → Logs)
2. Check build logs (Netlify dashboard → Deploys)
3. Verify environment variables are set correctly
4. Test API endpoints manually

---

## License

Copyright © 2024 MJ WebTech Pvt. Ltd.

## Deployment Checklist

[ ] Project builds successfully (`python scripts/export_static.py`)
[ ] `.env.example` committed, real secrets not committed
[ ] `.gitignore` updated
[ ] `netlify.toml` added (for static export)
[ ] README updated with deployment steps

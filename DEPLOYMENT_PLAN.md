# Deployment Plan & API Setup

## Required APIs & Services

### 1. **Database (PostgreSQL)**
- **Options:**
  - Railway PostgreSQL (Free tier: $5/month)
  - Render PostgreSQL (Free tier available)
  - Supabase (Free tier: 500MB)
  - Neon (Free tier: 3GB)
  - Fly.io Postgres (Pay as you go)

**Recommended:** Railway or Neon (easiest setup)

### 2. **Email Service**
- **Resend** (Recommended - Free tier: 3,000 emails/month)
  - Sign up: https://resend.com
  - Get API key from dashboard
  - Set up domain (or use their test domain)
  
- **Alternatives:**
  - SendGrid (Free: 100 emails/day)
  - Postmark (Free: 100 emails/month)
  - AWS SES (Pay as you go)

**Recommended:** Resend (simplest, good free tier)

### 3. **Hosting Platform**
- **Railway.app** (Recommended)
  - Free tier: $5 credit/month
  - Auto-deploys from GitHub
  - Built-in PostgreSQL
  - Easy environment variables
  
- **Alternatives:**
  - Render.com (Free tier available)
  - Fly.io (Free tier: 3 VMs)
  - Heroku (Paid only now)
  - DigitalOcean App Platform

## Setup Steps

### Step 1: Set Up Email Service (Resend)

1. **Sign up at https://resend.com**
2. **Get API Key:**
   - Go to API Keys section
   - Create new API key
   - Copy the key (starts with `re_`)

3. **Set up sending domain:**
   - Add your domain (or use test domain for testing)
   - Verify DNS records
   - Or use: `onboarding@resend.dev` for testing

### Step 2: Set Up Database

**Option A: Railway (Easiest)**
1. Go to https://railway.app
2. Create new project
3. Add PostgreSQL database
4. Copy connection string

**Option B: Neon (Free)**
1. Go to https://neon.tech
2. Create project
3. Copy connection string

### Step 3: Configure GitHub Secrets

Go to your GitHub repo → Settings → Secrets and variables → Actions

Add these secrets:
- `DATABASE_URL` - Your PostgreSQL connection string
- `EMAIL_API_KEY` - Your Resend API key (e.g., `re_xxxxxxxxxxxxx`)
- `EMAIL_FROM` - Your sender email (e.g., `noreply@yourdomain.com` or `onboarding@resend.dev`)

### Step 4: Deploy Application

**Option A: Railway (Recommended)**
1. Connect GitHub repo to Railway
2. Railway auto-detects Docker
3. Add environment variables:
   - `DATABASE_URL` (from Railway PostgreSQL)
   - `EMAIL_API_KEY`
   - `EMAIL_FROM`
4. Deploy!

**Option B: Render**
1. Create new Web Service
2. Connect GitHub repo
3. Use Docker
4. Add environment variables
5. Add PostgreSQL database
6. Deploy!

## GitHub Actions Setup

The workflows are already configured in:
- `.github/workflows/scrape.yml` - Runs every 30 minutes
- `.github/workflows/deploy.yml` - Deploys on push (if needed)

## Scheduled Jobs

### Automatic (via GitHub Actions)
- **Scraper:** Every 30 minutes
- **Alert Check:** Every 30 minutes (after scraper)
- **Daily Digest:** At configured time (7 AM by default)

### Manual Commands
```bash
# Send digest now
python -m cli digest

# Check and send alert
python -m cli alert

# Run scraper
python -m cli ingest
```

## Environment Variables

Create `.env` file or set in hosting platform:

```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
EMAIL_API_KEY=re_xxxxxxxxxxxxx
EMAIL_FROM=noreply@yourdomain.com
SCRAPE_INTERVAL_MINUTES=30
```

## Cost Estimate

**Free Tier Options:**
- Railway: $5/month credit (usually enough)
- Resend: 3,000 emails/month free
- GitHub Actions: 2,000 minutes/month free

**Total: ~$0-5/month** for small usage

## Next Steps

1. ✅ Set up Resend account
2. ✅ Set up PostgreSQL database
3. ✅ Add GitHub secrets
4. ✅ Deploy to Railway/Render
5. ✅ Test scraper
6. ✅ Test email sending
7. ✅ Monitor logs

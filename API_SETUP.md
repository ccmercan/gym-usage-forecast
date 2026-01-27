# API Setup Guide

## 1. Resend Email API (Recommended)

### Sign Up
1. Go to https://resend.com
2. Sign up for free account
3. Verify your email

### Get API Key
1. Go to **API Keys** in dashboard
2. Click **Create API Key**
3. Name it (e.g., "RecApp Production")
4. Copy the key (starts with `re_`)
5. **Save it immediately** - you can't see it again!

### Set Up Sender
**Option A: Use Test Domain (Quick)**
- Use: `onboarding@resend.dev`
- Works immediately, no setup needed
- Good for testing

**Option B: Use Your Domain (Production)**
1. Go to **Domains** in dashboard
2. Click **Add Domain**
3. Enter your domain (e.g., `yourdomain.com`)
4. Add DNS records:
   - SPF record
   - DKIM records
   - DMARC record (optional)
5. Wait for verification (usually < 5 minutes)

### Add to GitHub Secrets
- Secret name: `EMAIL_API_KEY`
- Value: Your API key (e.g., `re_xxxxxxxxxxxxx`)

- Secret name: `EMAIL_FROM`
- Value: `onboarding@resend.dev` (test) or `noreply@yourdomain.com` (production)

### Limits
- **Free tier:** 3,000 emails/month
- **Paid:** $20/month for 50,000 emails

---

## 2. PostgreSQL Database

### Option A: Railway (Easiest)

1. **Sign up:** https://railway.app
2. **Create project**
3. **Add PostgreSQL:**
   - Click **+ New**
   - Select **PostgreSQL**
   - Wait for provisioning
4. **Get connection string:**
   - Click on PostgreSQL service
   - Go to **Variables** tab
   - Copy `DATABASE_URL`

**Add to GitHub Secrets:**
- Secret name: `DATABASE_URL`
- Value: Connection string from Railway

### Option B: Neon (Free Tier)

1. **Sign up:** https://neon.tech
2. **Create project**
3. **Get connection string:**
   - Copy from dashboard
   - Format: `postgresql://user:pass@host/dbname`

**Add to GitHub Secrets:**
- Secret name: `DATABASE_URL`
- Value: Connection string from Neon

### Option C: Supabase

1. **Sign up:** https://supabase.com
2. **Create project**
3. **Get connection string:**
   - Go to Settings → Database
   - Copy connection string

**Add to GitHub Secrets:**
- Secret name: `DATABASE_URL`
- Value: Connection string from Supabase

---

## 3. Alternative Email Services

### SendGrid

1. **Sign up:** https://sendgrid.com
2. **Create API key**
3. **Update code:**
   - Change `notifications/email.py` to use SendGrid API
   - Endpoint: `https://api.sendgrid.com/v3/mail/send`

### Postmark

1. **Sign up:** https://postmarkapp.com
2. **Get server API token**
3. **Update code:**
   - Change `notifications/email.py` to use Postmark API
   - Endpoint: `https://api.postmarkapp.com/email`

---

## Quick Start Checklist

- [ ] Sign up for Resend
- [ ] Get Resend API key
- [ ] Set up sender email (test or custom domain)
- [ ] Sign up for PostgreSQL (Railway/Neon/Supabase)
- [ ] Get database connection string
- [ ] Add all secrets to GitHub
- [ ] Test workflow manually
- [ ] Verify emails are received

## Testing

### Test Email Locally
```bash
# Set environment variables
export EMAIL_API_KEY=re_xxxxxxxxxxxxx
export EMAIL_FROM=onboarding@resend.dev
export DATABASE_URL=postgresql://...

# Test email sending
python -m cli digest
```

### Test in GitHub Actions
1. Go to Actions tab
2. Run workflow manually
3. Check logs for email sending status

## Support

- **Resend Docs:** https://resend.com/docs
- **Railway Docs:** https://docs.railway.app
- **Neon Docs:** https://neon.tech/docs

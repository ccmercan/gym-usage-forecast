# Setting Up GitHub Actions

## Quick Setup Guide

### 1. Add GitHub Secrets

Go to your GitHub repository:
1. Click **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add these secrets:

#### Required Secrets:

**DATABASE_URL**
```
postgresql://user:password@host:5432/dbname
```
- Get this from your PostgreSQL provider (Railway, Neon, etc.)

**EMAIL_API_KEY**
```
re_xxxxxxxxxxxxx
```
- Get from Resend dashboard: https://resend.com/api-keys

**EMAIL_FROM**
```
noreply@yourdomain.com
```
- Or use Resend test email: `onboarding@resend.dev`

### 2. Enable GitHub Actions

1. Go to **Actions** tab in your GitHub repo
2. If prompted, click **"I understand my workflows, go ahead and enable them"**
3. Workflows will run automatically

### 3. Test the Workflows

**Manual Test:**
1. Go to **Actions** tab
2. Click on **"Scrape & Notify"** workflow
3. Click **"Run workflow"** → **"Run workflow"**
4. Watch it execute

**Check Results:**
- View logs in Actions tab
- Check your database for new data
- Check email inbox for alerts/digests

## Workflow Schedules

### Scrape & Notify (Every 30 minutes)
- Runs scraper to collect data
- Checks for low usage alerts
- Sends alert if conditions met (once per day)

### Daily Digest (7 AM UTC daily)
- Sends daily email with recommendations
- Adjust time in `.github/workflows/scrape.yml` if needed

## Customizing Schedule

Edit `.github/workflows/scrape.yml`:

```yaml
schedule:
  - cron: '*/30 * * * *'  # Every 30 minutes
  # Format: minute hour day month weekday
  # Examples:
  # '0 7 * * *' = 7 AM daily
  # '*/15 * * * *' = Every 15 minutes
  # '0 9 * * 1-5' = 9 AM weekdays only
```

## Troubleshooting

### Workflows not running?
- Check if Actions are enabled in repo settings
- Verify secrets are set correctly
- Check Actions tab for error messages

### Database connection errors?
- Verify `DATABASE_URL` secret is correct
- Check if database allows connections from GitHub IPs
- Some providers need IP whitelisting

### Email not sending?
- Verify `EMAIL_API_KEY` is correct
- Check `EMAIL_FROM` is valid
- Check Resend dashboard for delivery status
- Verify domain is verified (if using custom domain)

### Playwright errors?
- GitHub Actions installs dependencies automatically
- If issues persist, check the logs in Actions tab

## Monitoring

- **View logs:** Actions tab → Click on workflow run
- **Check database:** Query your PostgreSQL to see new data
- **Email delivery:** Check Resend dashboard for email status

## Cost

GitHub Actions free tier:
- **2,000 minutes/month** for private repos
- **Unlimited** for public repos
- Each workflow run uses ~2-3 minutes
- ~1,000 runs/month on free tier

## Next Steps

1. ✅ Add secrets to GitHub
2. ✅ Enable Actions
3. ✅ Test manual run
4. ✅ Monitor first scheduled run
5. ✅ Verify emails are received

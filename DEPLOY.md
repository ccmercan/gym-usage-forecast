# Deployment Guide

## Option 1: Docker Compose (Local/Server)

### Setup

1. **On your server/machine:**
   ```bash
   git clone <your-repo>
   cd RecApp
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Start services:**
   ```bash
   docker-compose up -d
   ```

3. **Initialize database:**
   ```bash
   docker-compose exec app alembic upgrade head
   ```

4. **Set up scheduled scraping (cron):**
   ```bash
   # Edit crontab
   crontab -e
   
   # Add this line to run scraper every 30 minutes:
   */30 * * * * cd /path/to/RecApp && docker-compose exec -T app python -m cli ingest
   ```

## Option 2: Cloud Deployment (Recommended)

### Railway.app

1. **Connect your GitHub repo to Railway**
2. **Add environment variables:**
   - `DATABASE_URL` (Railway provides PostgreSQL)
   - `EMAIL_API_KEY` (optional)
   - `EMAIL_FROM` (optional)

3. **Deploy** - Railway auto-detects Docker

4. **Set up scheduled jobs:**
   - Use Railway Cron or external cron service
   - Or use GitHub Actions (see below)

### Render.com

1. **Create Web Service** from Docker
2. **Add PostgreSQL database**
3. **Set environment variables**
4. **Use Render Cron Jobs** for scraping

### Fly.io

1. **Install flyctl:** `curl -L https://fly.io/install.sh | sh`
2. **Deploy:**
   ```bash
   fly launch
   fly postgres create
   fly secrets set DATABASE_URL=...
   fly deploy
   ```

## Option 3: GitHub Actions (Free Cron)

Create `.github/workflows/scrape.yml`:

```yaml
name: Scrape Facility Data

on:
  schedule:
    - cron: '*/30 * * * *'  # Every 30 minutes
  workflow_dispatch:  # Manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      - name: Run scraper
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: python -m cli ingest
```

## Production Checklist

- [ ] Set up production database (PostgreSQL)
- [ ] Configure environment variables
- [ ] Set up scheduled scraping (cron/GitHub Actions)
- [ ] Configure email service (Resend/SendGrid/Postmark)
- [ ] Set up monitoring/logging
- [ ] Configure domain/SSL (if needed)
- [ ] Test scraper with real TTU website
- [ ] Monitor initial scrapes for errors

## Monitoring

```bash
# Check logs
docker-compose logs -f app

# Check scraper runs
docker-compose exec app python -c "from app.db import SessionLocal; from app import models; db = SessionLocal(); print(f'Total snapshots: {db.query(models.UsageSnapshot).count()}')"
```

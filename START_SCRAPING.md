# Start Scraping Real Data

## Quick Start

### 1. Test the Scraper First

Before setting up automatic scraping, test it manually:

```bash
# If using Docker
docker-compose exec app python -m cli ingest

# If running locally
make ingest
```

**Check the output:**
- Should show "Found X facilities" with names and percentages
- Should show "Stored X new snapshots"
- If it says "No locations found", the page structure may have changed

### 2. Set Up Automatic Scraping

#### Option A: Using Cron (Linux/Mac)

```bash
# Run the setup script
./scripts/setup_cron.sh

# Or manually add to crontab
crontab -e
# Add this line:
*/30 * * * * cd /path/to/RecApp && docker-compose exec -T app python -m cli ingest >> logs/scraper.log 2>&1
```

#### Option B: Using GitHub Actions (Free, Cloud-based)

1. **Push your code to GitHub**
2. **Add secrets in GitHub Settings → Secrets:**
   - `DATABASE_URL` - Your production database URL
   - `EMAIL_API_KEY` (optional)
   - `EMAIL_FROM` (optional)

3. **The workflow is already set up** in `.github/workflows/scrape.yml`
   - Runs every 30 minutes automatically
   - Can also be triggered manually from GitHub Actions tab

#### Option C: Using Cloud Platform Cron

- **Railway:** Use Railway Cron Jobs
- **Render:** Use Render Cron Jobs  
- **Fly.io:** Use fly.toml with process groups

### 3. Monitor Scraping

```bash
# Check scraper logs
tail -f logs/scraper.log

# Or if using Docker
docker-compose logs -f app | grep -i scrape

# Check database for new data
docker-compose exec app python -c "
from app.db import SessionLocal
from app import models
from datetime import datetime, timedelta
db = SessionLocal()
recent = db.query(models.UsageSnapshot).filter(
    models.UsageSnapshot.scraped_at_utc >= datetime.utcnow() - timedelta(hours=1)
).count()
total = db.query(models.UsageSnapshot).count()
print(f'Recent (last hour): {recent}')
print(f'Total snapshots: {total}')
"
```

### 4. Troubleshooting

**If scraper finds no data:**
1. Check the TTU website is accessible
2. The page structure may have changed - check the HTML
3. Run with debug output:
   ```bash
   docker-compose exec app python -m cli ingest
   ```
4. Check the output for "No locations found" message

**If scraper fails:**
- Check logs: `docker-compose logs app`
- Verify database connection
- Check Playwright is installed: `docker-compose exec app playwright --version`

## Production Deployment

See [DEPLOY.md](DEPLOY.md) for full deployment instructions.

### Recommended: Railway.app

1. Connect GitHub repo
2. Railway auto-detects Docker
3. Add PostgreSQL database
4. Set environment variables
5. Use Railway Cron or GitHub Actions for scheduling

### Quick Deploy Commands

```bash
# Test locally first
docker-compose up -d
docker-compose exec app python -m cli ingest

# Then deploy to your platform
# (Follow platform-specific instructions in DEPLOY.md)
```

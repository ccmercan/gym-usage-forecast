# Raider Power Zone Forecasting

TTU recreation center usage monitoring and forecasting system.

**Data Source**: [Live Facility Counts](https://www.depts.ttu.edu/recreation/facilities/hours.php)  
*Note: Data is manually updated by TTU University Recreation. This system is read-only.*

## 🚀 Quick Deployment

See [DEPLOYMENT_PLAN.md](DEPLOYMENT_PLAN.md) for complete setup guide.

**Quick steps:**
1. Set up [Resend](https://resend.com) for emails
2. Set up PostgreSQL (Railway/Neon)
3. Add secrets to GitHub
4. Deploy to Railway/Render
5. Done! 🎉

## Architecture

```
┌─────────────┐
│   Scraper   │──┐
│ (hours.php) │  │
└─────────────┘  │
                 ├──> Postgres ──> Analytics ──> UI/Dashboard
┌─────────────┐  │
│   Email     │──┘
└─────────────┘
```

## Modules

- `ingestion/` - Web scraping from TTU hours.php (Playwright)
- `analytics/` - Recommendations and heatmap data
- `notifications/` - Email digest
- `app/` - FastAPI routes, templates, models

## Setup

1. Copy `.env.example` to `.env` and configure
2. Run with Docker Compose:
   ```bash
   docker-compose up
   ```
3. Initialize database:
   ```bash
   alembic upgrade head
   ```

## Usage

- `make dev` - Start API server
- `make ingest` - Run scraper
- `make digest` - Send email digest

## Quick Start

See [RUN.md](RUN.md) for detailed instructions.

**Quick version:**
```bash
# 1. Copy env file
cp .env.example .env

# 2. Start with Docker
docker-compose up -d

# 3. Initialize database
docker-compose exec app alembic upgrade head

# 4. Access UI
open http://localhost:8000
```

## Local Development

```bash
pip install -r requirements.txt
playwright install chromium
make dev
```

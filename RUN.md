# How to Run the Project

## Quick Start (Docker - Recommended)

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Start services:**
   ```bash
   docker-compose up -d
   ```

3. **Initialize database:**
   ```bash
   docker-compose exec app alembic upgrade head
   ```

4. **Access the UI:**
   - Open http://localhost:8000 in your browser

5. **Run ingestion (collect data):**
   ```bash
   docker-compose exec app python -m cli ingest
   ```

## Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your database URL
   ```

3. **Start database (if not using Docker):**
   ```bash
   docker-compose up -d db
   ```

4. **Initialize database:**
   ```bash
   alembic upgrade head
   ```

5. **Run the app:**
   ```bash
   make dev
   # Or: uvicorn app.main:app --reload
   ```

6. **Access UI:**
   - http://localhost:8000

## Common Commands

- **Start API server:** `make dev` or `uvicorn app.main:app --reload`
- **Run scraper:** `make ingest` or `python -m cli ingest`
- **Send email digest:** `make digest` or `python -m cli digest`

## First Time Setup

1. Start the application
2. Go to http://localhost:8000/settings
3. Configure your preferences:
   - Email address
   - Preferred time window
   - Crowd tolerance
   - Areas of interest
4. Run `make ingest` to collect initial data
5. View dashboard at http://localhost:8000/dashboard

## Troubleshooting

### Docker Daemon Not Running

If you see: `Cannot connect to the Docker daemon... Is the docker daemon running?`

**On macOS:**
1. Open Docker Desktop application
2. Wait for it to fully start (whale icon in menu bar)
3. Try again: `docker-compose up -d`

**Alternative - Run without Docker:**
1. Install PostgreSQL locally (via Homebrew: `brew install postgresql@16`)
2. Start PostgreSQL: `brew services start postgresql@16`
3. Create database: `createdb recapp`
4. Update `.env`: `DATABASE_URL=postgresql://localhost:5432/recapp`
5. Run: `make dev`

### Other Issues

- **Database connection error:** Make sure PostgreSQL is running (`docker-compose up -d db` or `brew services start postgresql@16`)
- **No data on dashboard:** Run `make ingest` to collect facility data
- **Scraper errors:** Check that the TTU website is accessible and structure hasn't changed
- **Port 8000 already in use:** Change port in `docker-compose.yml` or use `uvicorn app.main:app --port 8001`

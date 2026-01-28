# Raider Power Zone Forecasting

TTU recreation center usage monitoring and forecasting system.

**🌐 Live Application**: [https://gym-usage-forecast-production.up.railway.app/](https://gym-usage-forecast-production.up.railway.app/)

**Data Source**: [Live Facility Counts](https://www.depts.ttu.edu/recreation/facilities/hours.php)  
*Note: Data is manually updated by TTU University Recreation. This system is read-only.*


Visit the live application at **[https://gym-usage-forecast-production.up.railway.app/](https://gym-usage-forecast-production.up.railway.app/)** to:
- Configure your preferences (preferred workout times, areas of interest, crowd tolerance)
- View real-time recommendations for the best times to visit
- See usage heatmaps showing average crowd levels by day and hour
- Set up daily email digests with personalized recommendations

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

## 🛠️ For Developers

### Local Development Setup

If you want to run this project locally for development:

```bash
pip install -r requirements.txt
playwright install chromium
make dev
```

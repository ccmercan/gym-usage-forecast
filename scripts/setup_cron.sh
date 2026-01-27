#!/bin/bash
# Setup cron job for automatic scraping

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Setting up cron job for RecApp scraper..."
echo "This will run the scraper every 30 minutes"

# Get the full path to docker-compose
DOCKER_COMPOSE_CMD="docker-compose"

# Check if running in Docker or locally
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo "Error: docker-compose not found"
    exit 1
fi

# Create cron jobs
CRON_INGEST="*/30 * * * * cd $PROJECT_DIR && $DOCKER_COMPOSE_CMD exec -T app python -m cli ingest >> $PROJECT_DIR/logs/scraper.log 2>&1"
CRON_ALERT="*/30 * * * * cd $PROJECT_DIR && $DOCKER_COMPOSE_CMD exec -T app python -m cli alert >> $PROJECT_DIR/logs/alert.log 2>&1"
CRON_DIGEST="0 7 * * * cd $PROJECT_DIR && $DOCKER_COMPOSE_CMD exec -T app python -m cli digest >> $PROJECT_DIR/logs/digest.log 2>&1"

# Check if cron jobs already exist
if crontab -l 2>/dev/null | grep -q "cli ingest"; then
    echo "Cron jobs already exist. Removing old ones..."
    crontab -l 2>/dev/null | grep -v "cli ingest\|cli alert\|cli digest" | crontab -
fi

# Add new cron jobs
(crontab -l 2>/dev/null; echo "$CRON_INGEST"; echo "$CRON_ALERT"; echo "$CRON_DIGEST") | crontab -

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

echo "✅ Cron jobs installed!"
echo "   Scraper: Every 30 minutes"
echo "   Alerts: Every 30 minutes (checks for low usage)"
echo "   Digest: Daily at 7:00 AM"
echo "   Logs: $PROJECT_DIR/logs/"
echo ""
echo "View cron jobs: crontab -l"
echo "Remove cron job: crontab -e (then delete the line)"

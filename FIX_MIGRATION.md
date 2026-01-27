# Fix Migration Issue

The tables already exist in your database. You have two options:

## Option 1: Stamp the database (Recommended)

Tell Alembic that the migration is already applied:

```bash
docker-compose exec app alembic stamp head
```

Then you can proceed normally. The database is now in sync with Alembic.

## Option 2: Drop and recreate (if you don't need existing data)

If you don't have important data, you can reset:

```bash
# Stop containers
docker-compose down

# Remove the database volume
docker volume rm recapp_postgres_data

# Start fresh
docker-compose up -d

# Wait a few seconds, then run migration
docker-compose exec app alembic upgrade head
```

## After fixing

Once the migration is resolved, you can:

1. **Access the UI:** http://localhost:8000
2. **Run scraper:** `docker-compose exec app python -m cli ingest`

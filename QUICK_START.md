# Quick Start Guide

## After Docker is Running

**1. Rebuild the Docker image (to fix the Python path):**
```bash
docker-compose build
```

**2. Start services:**
```bash
docker-compose up -d
```

**3. Wait 5-10 seconds for database to be ready, then initialize:**
```bash
docker-compose exec app alembic upgrade head
```

**4. Open the UI:**
```
http://localhost:8000
```

**5. (Optional) Collect data:**
```bash
docker-compose exec app python -m cli ingest
```

## Check Status

```bash
# Check if containers are running
docker-compose ps

# View logs
docker-compose logs -f app

# Check database connection
docker-compose exec app python -c "from app.db import engine; print('DB OK' if engine else 'DB Error')"
```

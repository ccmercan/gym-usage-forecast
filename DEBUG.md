# Debugging Internal Server Error

## Check Docker Logs

```bash
# View app logs
docker-compose logs app

# View recent logs with timestamps
docker-compose logs --tail=50 app

# Follow logs in real-time
docker-compose logs -f app
```

## Common Issues

### 1. Database Connection Error

**Symptoms:** `OperationalError`, `connection refused`, `database does not exist`

**Fix:**
```bash
# Check if database is running
docker-compose ps

# Check database connection
docker-compose exec app python -c "from app.db import engine; engine.connect(); print('OK')"

# Verify DATABASE_URL in .env
docker-compose exec app cat .env
```

### 2. Missing Environment Variables

**Fix:**
```bash
# Check .env file exists
ls -la .env

# Verify DATABASE_URL is set
docker-compose exec app env | grep DATABASE_URL
```

### 3. Template Not Found

**Symptoms:** `TemplateNotFound` error

**Fix:**
```bash
# Check templates directory exists
docker-compose exec app ls -la app/templates/
```

### 4. Import Errors

**Symptoms:** `ModuleNotFoundError`, `ImportError`

**Fix:**
```bash
# Rebuild container
docker-compose build app
docker-compose up -d
```

## Quick Test

```bash
# Test database connection
docker-compose exec app python -c "
from app.db import engine
from app.config import settings
print(f'DB URL: {settings.database_url}')
conn = engine.connect()
print('Database connection: OK')
conn.close()
"

# Test app import
docker-compose exec app python -c "
from app.main import app
print('App import: OK')
"
```

## View Error Details

The app now has detailed error handling. Check:
1. Browser console (F12)
2. Docker logs: `docker-compose logs app`
3. The error response will show traceback in development

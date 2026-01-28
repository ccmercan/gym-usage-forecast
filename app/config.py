from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # Railway provides DATABASE_URL automatically - prioritize env var over .env file
    database_url: str = os.getenv("DATABASE_URL", "")
    email_api_key: str = ""
    email_from: str = ""
    scrape_interval_minutes: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Environment variables take precedence over .env file
        env_file_required = False

# Try to load settings, with fallback
try:
    settings = Settings()
    # Ensure DATABASE_URL is set - Railway provides this automatically
    if not settings.database_url:
        # Fallback for local development
        settings.database_url = os.getenv("DATABASE_URL", "postgresql://recapp:recapp@localhost:5432/recapp")
    
    # Log database URL (masked for security)
    db_url_masked = settings.database_url
    if "@" in db_url_masked:
        parts = db_url_masked.split("@")
        if len(parts) == 2:
            db_url_masked = "***@" + parts[1]
    print(f"Database URL configured: {db_url_masked}")
except Exception as e:
    print(f"Warning: Error loading settings: {e}")
    # Fallback settings - prioritize DATABASE_URL from environment
    database_url = os.getenv("DATABASE_URL", "postgresql://recapp:recapp@localhost:5432/recapp")
    settings = Settings(
        database_url=database_url
    )

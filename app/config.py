from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    database_url: str = ""
    email_api_key: str = ""
    email_from: str = ""
    scrape_interval_minutes: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Try to load settings, with fallback
try:
    settings = Settings()
    if not settings.database_url:
        # Fallback for Docker
        settings.database_url = os.getenv("DATABASE_URL", "postgresql://recapp:recapp@db:5432/recapp")
except Exception as e:
    print(f"Warning: Error loading settings: {e}")
    # Fallback settings
    settings = Settings(
        database_url=os.getenv("DATABASE_URL", "postgresql://recapp:recapp@db:5432/recapp")
    )

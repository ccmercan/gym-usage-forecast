from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from app.config import settings
import logging
import os

logger = logging.getLogger(__name__)

# Log database configuration for debugging
database_url = settings.database_url or os.getenv("DATABASE_URL", "")
if not database_url:
    logger.error("DATABASE_URL is not set! Please configure it in Railway or environment variables.")
    raise ValueError("DATABASE_URL environment variable is required")

# Mask password in logs
db_url_for_log = database_url
if "@" in db_url_for_log:
    try:
        parts = db_url_for_log.split("@")
        if len(parts) == 2:
            db_url_for_log = "***@" + parts[1]
    except:
        pass

logger.info(f"Initializing database connection: {db_url_for_log}")

try:
    engine = create_engine(
        database_url,
        pool_pre_ping=True,  # Verify connections before using
        echo=False,
        pool_size=5,
        max_overflow=10
    )
    SessionLocal = sessionmaker(bind=engine)
    Base = declarative_base()
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    logger.error(f"Database URL (masked): {db_url_for_log}")
    raise

def get_db():
    db = SessionLocal()
    try:
        yield db
    except OperationalError as e:
        logger.error(f"Database connection error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

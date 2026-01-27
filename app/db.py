from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from app.config import settings
import logging

logger = logging.getLogger(__name__)

try:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,  # Verify connections before using
        echo=False
    )
    SessionLocal = sessionmaker(bind=engine)
    Base = declarative_base()
    logger.info(f"Database engine created: {settings.database_url[:20]}...")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
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

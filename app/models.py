from sqlalchemy import Column, Integer, String, DateTime, ARRAY
from datetime import datetime
from app.db import Base

class UsageSnapshot(Base):
    __tablename__ = "usage_snapshots"
    
    id = Column(Integer, primary_key=True)
    timestamp_utc = Column(DateTime, nullable=False)
    location_name = Column(String, nullable=False)
    usage_percentage = Column(Integer, nullable=False)
    scraped_at_utc = Column(DateTime, default=datetime.utcnow)
    parser_version = Column(String, default="1.0")

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, default=1)
    email = Column(String, nullable=False)
    timezone = Column(String, default="America/Chicago")  # Always Texas time
    preferred_start_time_local = Column(String)
    preferred_end_time_local = Column(String)
    preferred_days = Column(ARRAY(Integer))
    areas_of_interest = Column(ARRAY(String))
    crowd_tolerance_pct = Column(Integer, default=50)
    digest_send_time_local = Column(String)
    workout_duration_minutes = Column(Integer, default=60, server_default='60')  # Duration in minutes
    last_alert_sent_date = Column(DateTime, nullable=True)  # Track when alert was last sent

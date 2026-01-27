#!/usr/bin/env python3
"""Generate sample facility usage data for testing."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from app.db import SessionLocal
from app import models
from app.constants import TTU_FACILITIES
import random

def generate_sample_data():
    """Generate sample data with busy periods 4pm-8pm Mon-Fri."""
    db = SessionLocal()
    
    # Use TTU Recreation Center facilities
    facilities = TTU_FACILITIES
    
    # Generate data for the last 14 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=14)
    
    # Generate snapshots every 30 minutes
    current = start_date
    snapshots_created = 0
    
    while current <= end_date:
        weekday = current.weekday()  # 0=Monday, 6=Sunday
        hour = current.hour
        
        for facility in facilities:
            # Busy between 4pm (16) and 8pm (20) on weekdays (Mon-Fri, 0-4)
            if weekday < 5 and 16 <= hour < 20:
                # Busy: 60-90% usage
                usage = random.randint(60, 90)
            else:
                # Random: 10-50% usage
                usage = random.randint(10, 50)
            
            # Check if snapshot already exists (avoid duplicates)
            existing = db.query(models.UsageSnapshot).filter(
                models.UsageSnapshot.location_name == facility,
                models.UsageSnapshot.timestamp_utc == current.replace(second=0, microsecond=0)
            ).first()
            
            if not existing:
                snapshot = models.UsageSnapshot(
                    timestamp_utc=current.replace(second=0, microsecond=0),
                    location_name=facility,
                    usage_percentage=usage,
                    scraped_at_utc=current,
                    parser_version="sample_data_1.0"
                )
                db.add(snapshot)
                snapshots_created += 1
        
        # Move to next 30-minute interval
        current += timedelta(minutes=30)
    
    try:
        db.commit()
        print(f"✅ Created {snapshots_created} sample snapshots")
        print(f"   Facilities: {', '.join(facilities)}")
        print(f"   Date range: {start_date.date()} to {end_date.date()}")
        print(f"   Busy periods: 4pm-8pm Mon-Fri (60-90% usage)")
        print(f"   Other times: Random 10-50% usage")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    generate_sample_data()

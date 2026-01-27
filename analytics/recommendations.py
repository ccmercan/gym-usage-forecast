from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app import models
import pytz

def get_recommendations(db: Session, prefs: models.UserPreferences):
    """Get recommended time ranges for today based on last 2 weeks of data.
    Returns time windows matching the user's workout duration."""
    # Get workout duration in minutes
    workout_duration = prefs.workout_duration_minutes or 60
    workout_hours = workout_duration / 60.0  # Convert to hours (e.g., 90 min = 1.5 hours)
    
    # Default to all day if not set
    if not prefs.preferred_start_time_local:
        start_hour = 6  # Facility opens at 6am
        start_min = 0
    else:
        start_hour, start_min = map(int, prefs.preferred_start_time_local.split(":"))
    
    if not prefs.preferred_end_time_local:
        end_hour = 23  # Facility closes at 12am (23:59)
        end_min = 59
    else:
        end_hour, end_min = map(int, prefs.preferred_end_time_local.split(":"))
    
    # Always use Texas time (America/Chicago)
    tz = pytz.timezone("America/Chicago")
    now = datetime.now(tz)
    
    # Get data from last 2 weeks for same weekday
    weekday = now.weekday()
    two_weeks_ago = now - timedelta(days=14)
    
    # If no areas specified, use all facilities
    query = db.query(models.UsageSnapshot).filter(
        models.UsageSnapshot.timestamp_utc >= two_weeks_ago.astimezone(pytz.UTC).replace(tzinfo=None)
    )
    if prefs.areas_of_interest:
        query = query.filter(models.UsageSnapshot.location_name.in_(prefs.areas_of_interest))
    
    snapshots = query.all()
    
    if not snapshots:
        return []
    
    # Group by 30-minute intervals for more granular analysis
    interval_usage = {}  # Key: (hour, half_hour), Value: list of percentages
    for snap in snapshots:
        snap_dt = pytz.UTC.localize(snap.timestamp_utc).astimezone(tz)
        if snap_dt.weekday() == weekday:
            hour = snap_dt.hour
            minute = snap_dt.minute
            half_hour = 0 if minute < 30 else 1
            interval_key = (hour, half_hour)
            
            # Convert to minutes since start of day
            time_minutes = hour * 60 + minute
            start_minutes = start_hour * 60 + start_min
            end_minutes = end_hour * 60 + end_min
            
            if start_minutes <= time_minutes < end_minutes:
                interval_usage.setdefault(interval_key, []).append(snap.usage_percentage)
    
    if not interval_usage:
        return []
    
    # Calculate average usage per 30-minute interval
    tolerance = prefs.crowd_tolerance_pct or 100
    interval_averages = {}
    for interval_key, vals in interval_usage.items():
        avg = sum(vals) / len(vals)
        if avg <= tolerance:
            interval_averages[interval_key] = avg
    
    if not interval_averages:
        return []
    
    # Find best time windows of the specified duration
    # Convert workout duration to number of 30-minute intervals
    num_intervals = int(workout_duration / 30)  # e.g., 90 min = 3 intervals
    
    # Generate all possible time windows of the specified duration
    windows = []
    start_minutes_total = start_hour * 60 + start_min
    end_minutes_total = end_hour * 60 + end_min
    
    # Try every 30-minute interval as a potential start time
    for start_minutes in range(start_minutes_total, end_minutes_total - workout_duration + 1, 30):
        end_minutes = start_minutes + workout_duration
        
        # Check if we have data for all intervals in this window
        window_intervals = []
        window_usage = []
        
        current_minutes = start_minutes
        valid_window = True
        
        while current_minutes < end_minutes:
            hour = current_minutes // 60
            minute = current_minutes % 60
            half_hour = 0 if minute < 30 else 1
            interval_key = (hour, half_hour)
            
            if interval_key in interval_averages:
                window_intervals.append(interval_key)
                window_usage.append(interval_averages[interval_key])
            else:
                # If we don't have data for an interval, skip this window
                valid_window = False
                break
            
            current_minutes += 30
        
        if valid_window and window_usage:
            # Calculate average usage for this window
            avg_usage = sum(window_usage) / len(window_usage)
            
            # Format time range
            start_h = start_minutes // 60
            start_m = start_minutes % 60
            end_h = end_minutes // 60
            end_m = end_minutes % 60
            
            if start_m == 0:
                start_str = f"{start_h}:00"
            else:
                start_str = f"{start_h}:{start_m:02d}"
            
            if end_m == 0:
                end_str = f"{end_h}:00"
            else:
                end_str = f"{end_h}:{end_m:02d}"
            
            time_str = f"{start_str}-{end_str}"
            windows.append((time_str, avg_usage, start_minutes))
    
    if not windows:
        return []
    
    # Sort by average usage (lowest first)
    windows.sort(key=lambda x: x[1])
    
    # Return top 3 windows
    return [(time_str, avg) for time_str, avg, _ in windows[:3]]

def get_heatmap_data(db: Session, prefs: models.UserPreferences):
    """Get day x hour heatmap data for selected area."""
    # If no areas specified, use all facilities
    query = db.query(models.UsageSnapshot)
    if prefs.areas_of_interest:
        query = query.filter(models.UsageSnapshot.location_name.in_(prefs.areas_of_interest))
    
    snapshots = query.limit(2000).all()
    
    if not snapshots:
        return {}
    
    # Always use Texas time (America/Chicago)
    tz = pytz.timezone("America/Chicago")
    heatmap = {}
    
    for snap in snapshots:
        snap_dt = pytz.UTC.localize(snap.timestamp_utc).astimezone(tz)
        key = (snap_dt.weekday(), snap_dt.hour)
        heatmap.setdefault(key, []).append(snap.usage_percentage)
    
    # Average per cell
    return {k: sum(v) / len(v) for k, v in heatmap.items()}

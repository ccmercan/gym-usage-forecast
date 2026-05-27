"""
Tool functions exposed to Gemini via function calling.

Each function queries PostgreSQL and returns structured data
that Gemini can reason over to produce a natural language answer.

Why 3 tools?
  - get_current_usage   → "how busy is it RIGHT NOW"
  - get_best_times      → "WHEN should I go" (uses existing analytics)
  - query_gym_data      → "show me PATTERNS" (arbitrary day/hour/facility filters)
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models
import pytz

TZ = pytz.timezone("America/Chicago")
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_current_usage(db: Session, facility: str = None) -> dict:
    """Return the most recent usage snapshot for one or all facilities."""
    query = db.query(models.UsageSnapshot)
    if facility:
        query = query.filter(models.UsageSnapshot.location_name.ilike(f"%{facility}%"))

    latest_time = query.with_entities(func.max(models.UsageSnapshot.timestamp_utc)).scalar()
    if not latest_time:
        return {"facilities": [], "message": "No usage data available yet."}

    # Pull everything within one scrape cycle of the latest timestamp
    cutoff = latest_time - timedelta(minutes=35)
    snapshots = (
        query.filter(models.UsageSnapshot.timestamp_utc >= cutoff)
        .order_by(models.UsageSnapshot.timestamp_utc.desc())
        .all()
    )

    results = []
    seen: set = set()
    for snap in snapshots:
        if snap.location_name not in seen:
            seen.add(snap.location_name)
            local_dt = pytz.UTC.localize(snap.timestamp_utc).astimezone(TZ)
            results.append(
                {
                    "facility": snap.location_name,
                    "usage_percentage": snap.usage_percentage,
                    "as_of": local_dt.strftime("%I:%M %p CST"),
                }
            )

    return {
        "facilities": results,
        "data_as_of": results[0]["as_of"] if results else "unknown",
    }


def get_best_times(
    db: Session,
    workout_duration_minutes: int = 60,
    weekday: str = None,
) -> dict:
    """Return the top 3 least-crowded workout windows from historical data."""
    from analytics.recommendations import get_recommendations

    prefs = db.query(models.UserPreferences).first()

    # Build a temporary prefs-like object so we can reuse the existing analytics
    class _TempPrefs:
        preferred_start_time_local = "06:00"
        preferred_end_time_local = "22:00"
        crowd_tolerance_pct = 100  # No filter — return all windows ranked
        areas_of_interest = []
        timezone = "America/Chicago"

    temp = _TempPrefs()
    temp.workout_duration_minutes = workout_duration_minutes
    if prefs and prefs.areas_of_interest:
        temp.areas_of_interest = prefs.areas_of_interest

    recommendations = get_recommendations(db, temp)

    return {
        "best_times": [
            {"time_range": time_range, "average_usage_pct": round(pct, 1)}
            for time_range, pct in recommendations
        ],
        "workout_duration_minutes": workout_duration_minutes,
        "day": weekday or "today (same weekday)",
    }


def query_gym_data(
    db: Session,
    facility: str = None,
    weekday: str = None,
    start_hour: int = None,
    end_hour: int = None,
) -> dict:
    """Query aggregated historical usage filtered by facility, weekday, and/or hour range."""
    # Query all history — no date filter so older data is included
    query = db.query(models.UsageSnapshot)
    if facility:
        query = query.filter(
            models.UsageSnapshot.location_name.ilike(f"%{facility}%")
        )

    snapshots = query.all()

    # Resolve weekday name → integer (0=Mon … 6=Sun)
    # Use explicit None check instead of `or` so that Monday (0) doesn't evaluate as falsy
    target_weekday = None
    if weekday:
        name_map = {name.lower(): i for i, name in enumerate(WEEKDAY_NAMES)}
        short_map = {name[:3].lower(): i for i, name in enumerate(WEEKDAY_NAMES)}
        resolved = name_map.get(weekday.lower())
        if resolved is None:
            resolved = short_map.get(weekday.lower()[:3])
        target_weekday = resolved

    hour_buckets: dict = {}
    for snap in snapshots:
        snap_local = pytz.UTC.localize(snap.timestamp_utc).astimezone(TZ)
        if target_weekday is not None and snap_local.weekday() != target_weekday:
            continue
        if start_hour is not None and snap_local.hour < start_hour:
            continue
        if end_hour is not None and snap_local.hour >= end_hour:
            continue
        key = (snap.location_name, snap_local.hour)
        hour_buckets.setdefault(key, []).append(snap.usage_percentage)

    results = [
        {
            "facility": fac,
            "hour": f"{hour}:00",
            "average_usage_pct": round(sum(vals) / len(vals), 1),
            "data_points": len(vals),
        }
        for (fac, hour), vals in sorted(hour_buckets.items())
    ]

    return {
        "results": results,
        "filters_applied": {
            "facility": facility,
            "weekday": weekday,
            "start_hour": start_hour,
            "end_hour": end_hour,
        },
    }

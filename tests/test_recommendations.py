from datetime import datetime
from unittest.mock import Mock

import pytz
from sqlalchemy.orm import Session


def test_recommendations_skip_windows_with_missing_occupancy(monkeypatch, tmp_path):
    # Model imports initialize an engine. Point it at a disposable URL even
    # though this test supplies snapshots through a mocked session.
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'unused.db'}")
    from analytics import get_recommendations, recommendations
    from app.models import UsageSnapshot, UserPreferences

    chicago = pytz.timezone("America/Chicago")
    monday_at_noon = chicago.localize(datetime(2026, 1, 12, 12))

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return monday_at_noon.replace(tzinfo=None)
            return monday_at_noon.astimezone(tz)

    monkeypatch.setattr(recommendations, "datetime", FixedDateTime)

    facility = "Free Weight Room"
    prefs = UserPreferences(
        preferred_start_time_local="16:00",
        preferred_end_time_local="19:00",
        workout_duration_minutes=60,
        crowd_tolerance_pct=50,
        areas_of_interest=[facility],
    )
    # Readings from the previous Monday, with the 16:30 slot missing.
    snapshots = [
        UsageSnapshot(
            location_name=facility,
            timestamp_utc=chicago.localize(datetime(2026, 1, 5, hour, minute))
            .astimezone(pytz.UTC)
            .replace(tzinfo=None),
            usage_percentage=usage,
        )
        for hour, minute, usage in [(16, 0, 20), (18, 0, 25), (18, 30, 30)]
    ]
    db = Mock(spec=Session)
    query = db.query.return_value
    query.filter.return_value = query
    query.all.return_value = snapshots

    windows = dict(get_recommendations(db, prefs))

    assert windows["18:00-19:00"] == 27.5
    assert "16:00-17:00" not in windows

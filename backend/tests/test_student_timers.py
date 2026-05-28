"""Day 12: student timer helpers."""

from datetime import datetime, timezone

from app.services.student_timer_service import is_time_expired, remaining_seconds


def test_remaining_seconds_counts_down():
    start = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    now = start.replace(second=25)
    left = remaining_seconds(60, start.isoformat(), now.timestamp())
    assert left == 35


def test_remaining_seconds_returns_none_when_unlimited():
    assert remaining_seconds(None, "2026-01-01T12:00:00+00:00", 0) is None
    assert remaining_seconds(0, "2026-01-01T12:00:00+00:00", 0) is None


def test_remaining_seconds_never_negative():
    from datetime import timedelta

    start = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    now = start + timedelta(seconds=90)
    left = remaining_seconds(30, start.isoformat(), now.timestamp())
    assert left == 0


def test_is_time_expired():
    assert is_time_expired(0) is True
    assert is_time_expired(1) is False
    assert is_time_expired(None) is False

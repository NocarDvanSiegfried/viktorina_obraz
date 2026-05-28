"""Pure helpers for student countdown timers (day 12)."""

from __future__ import annotations


def remaining_seconds(
    limit_seconds: int | None,
    started_at_iso: str | None,
    now_epoch_seconds: float,
) -> int | None:
    if limit_seconds is None or limit_seconds <= 0 or not started_at_iso:
        return None

    from datetime import datetime

    normalized = (
        started_at_iso.replace("Z", "+00:00")
        if started_at_iso.endswith("Z")
        else started_at_iso
    )
    started = datetime.fromisoformat(normalized)
    started_ts = started.timestamp()
    elapsed = int(now_epoch_seconds - started_ts)
    return max(0, int(limit_seconds) - elapsed)


def is_time_expired(remaining: int | None) -> bool:
    return remaining is not None and remaining <= 0

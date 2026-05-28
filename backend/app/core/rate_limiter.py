import math
import time
from typing import Dict, List, Tuple

from app.core.config import settings


class InMemoryRateLimiter:
    """Simple moving-window rate limiter for in-process throttling."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._events: Dict[str, List[float]] = {}

    def clear(self) -> None:
        self._events.clear()

    def allow(self, key: str) -> Tuple[bool, int]:
        now = time.monotonic()
        cutoff = now - self.window_seconds

        timestamps = self._events.get(key, [])
        timestamps = [t for t in timestamps if t >= cutoff]

        # Block before appending the new request.
        if len(timestamps) >= self.max_requests:
            earliest = min(timestamps) if timestamps else now
            retry_after_seconds = max(
                1, int(math.ceil(earliest + self.window_seconds - now))
            )
            self._events[key] = timestamps
            return False, retry_after_seconds

        timestamps.append(now)
        self._events[key] = timestamps
        return True, 0


rate_limiter = InMemoryRateLimiter(
    max_requests=settings.QUIZ_GENERATE_RATE_LIMIT_MAX_REQUESTS,
    window_seconds=settings.QUIZ_GENERATE_RATE_LIMIT_WINDOW_SECONDS,
)


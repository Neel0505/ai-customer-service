"""Simple rate limiter for webhook endpoints."""

from __future__ import annotations

import time
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimiter:
    """In-memory rate limiter (per user_id). For MVP — could use Redis in production."""

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, user_id: str) -> bool:
        """Check if a request from this user is within rate limits."""
        now = time.time()
        window_start = now - self.window

        # Clean old entries
        self._requests[user_id] = [
            ts for ts in self._requests[user_id] if ts > window_start
        ]

        if len(self._requests[user_id]) >= self.max_requests:
            logger.warning("Rate limit exceeded for user %s", user_id)
            return False

        self._requests[user_id].append(now)
        return True

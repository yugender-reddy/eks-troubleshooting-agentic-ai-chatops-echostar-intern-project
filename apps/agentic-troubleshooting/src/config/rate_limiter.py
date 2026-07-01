"""Rate limiter for AWS costly operations (Bedrock, S3 Vectors).

Prevents runaway costs by capping invocations per minute/hour.
"""

import time
import threading
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token-bucket rate limiter with per-minute and per-hour caps."""

    def __init__(self, per_minute: int = 20, per_hour: int = 200):
        self.per_minute = per_minute
        self.per_hour = per_hour
        self._minute_timestamps: list[float] = []
        self._hour_timestamps: list[float] = []
        self._lock = threading.Lock()

    def _prune(self, now: float):
        self._minute_timestamps = [t for t in self._minute_timestamps if now - t < 60]
        self._hour_timestamps = [t for t in self._hour_timestamps if now - t < 3600]

    def allow(self) -> bool:
        """Return True if the call is allowed, False if rate-limited."""
        with self._lock:
            now = time.time()
            self._prune(now)
            if len(self._minute_timestamps) >= self.per_minute:
                logger.warning("Rate limit hit (per-minute cap)")
                return False
            if len(self._hour_timestamps) >= self.per_hour:
                logger.warning("Rate limit hit (per-hour cap)")
                return False
            self._minute_timestamps.append(now)
            self._hour_timestamps.append(now)
            return True


# Shared limiters for different AWS services
# Bedrock inference: 20/min, 200/hr — covers classification + orchestration + specialist
bedrock_limiter = RateLimiter(per_minute=20, per_hour=200)

# Bedrock embeddings (Titan): 30/min, 300/hr — cheaper but still capped
embedding_limiter = RateLimiter(per_minute=30, per_hour=300)

# S3 Vectors: 30/min, 300/hr
s3vectors_limiter = RateLimiter(per_minute=30, per_hour=300)

RATE_LIMIT_MSG = "⚠️ Rate limit reached — too many requests. Please wait a moment before trying again."

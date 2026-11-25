"""Redis-backed API-key rate limiting."""
from __future__ import annotations

import hashlib
import time

from fastapi import HTTPException, status
from redis.exceptions import RedisError

from app.config import settings
from app.redis_client import r


WINDOW_SECONDS = 60


def _bucket_key(api_key: str, now: float) -> str:
    """Do not place raw credentials in Redis keys."""
    key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    return f"agent:rate-limit:{key_hash}:{int(now // WINDOW_SECONDS)}"


def check_rate_limit(key: str) -> None:
    """Consume one request slot or return HTTP 429 with retry guidance."""
    now = time.time()
    redis_key = _bucket_key(key, now)
    retry_after = max(1, WINDOW_SECONDS - int(now % WINDOW_SECONDS))
    try:
        # INCR is atomic, therefore all workers and restarts share one limit.
        count = int(r.incr(redis_key))
        if count == 1:
            r.expire(redis_key, WINDOW_SECONDS + 1)
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiter is temporarily unavailable",
        ) from exc
    if count > settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )

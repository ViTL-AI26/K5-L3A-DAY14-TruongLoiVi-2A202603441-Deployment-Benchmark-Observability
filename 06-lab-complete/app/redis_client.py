"""Shared, lazily-connecting Redis client."""
from __future__ import annotations

from redis import Redis
from redis.exceptions import RedisError

from app.config import settings


# Creating the client does not contact Redis, so liveness can always start.
r: Redis = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
    health_check_interval=30,
)


def redis_healthy() -> bool:
    try:
        return bool(r.ping())
    except RedisError:
        return False

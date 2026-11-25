"""Daily LLM spend guard with Redis as the shared source of truth."""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from redis.exceptions import RedisError

from app.config import settings
from app.redis_client import r


PRICE_INPUT_PER_1K = 0.00015
PRICE_OUTPUT_PER_1K = 0.0006
_COST_TTL_SECONDS = 2 * 24 * 60 * 60


def _cost_key() -> str:
    return f"agent:daily-cost:{datetime.now(UTC).date().isoformat()}"


def check_budget() -> None:
    """Reject requests after the shared daily budget has been exhausted."""
    try:
        spent = float(r.get(_cost_key()) or 0.0)
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cost guard is temporarily unavailable",
        ) from exc
    if spent >= settings.daily_budget_usd:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Daily LLM budget exhausted",
        )


def record_cost(input_tokens: int, output_tokens: int) -> float:
    """Persist the request cost and return it for structured logging."""
    cost = (
        max(0, input_tokens) / 1000 * PRICE_INPUT_PER_1K
        + max(0, output_tokens) / 1000 * PRICE_OUTPUT_PER_1K
    )
    try:
        key = _cost_key()
        r.incrbyfloat(key, cost)
        r.expire(key, _COST_TTL_SECONDS)
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cost guard is temporarily unavailable",
        ) from exc
    return cost

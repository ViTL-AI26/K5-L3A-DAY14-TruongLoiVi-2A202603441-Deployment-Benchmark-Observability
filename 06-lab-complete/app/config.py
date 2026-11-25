"""Application settings loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _int_env(name: str, default: int, minimum: int = 1) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value >= minimum else default


def _float_env(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value >= 0 else default


@dataclass(frozen=True)
class Settings:
    port: int
    environment: str
    agent_api_key: str
    redis_url: str
    rate_limit_per_minute: int
    daily_budget_usd: float


def load_settings() -> Settings:
    """Build settings once for each uvicorn worker."""
    return Settings(
        port=_int_env("PORT", 8000),
        environment=os.getenv("ENVIRONMENT", "development"),
        agent_api_key=os.getenv("AGENT_API_KEY", ""),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        rate_limit_per_minute=_int_env("RATE_LIMIT_PER_MINUTE", 10),
        daily_budget_usd=_float_env("DAILY_BUDGET_USD", 10.0),
    )


settings = load_settings()

"""Production-ready FastAPI application for the Part 6 mock AI agent."""
from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.auth import verify_api_key
from app.cost_guard import check_budget, record_cost
from app.rate_limiter import check_rate_limit
from app.redis_client import redis_healthy
from utils.mock_llm import ask as llm_ask


class JsonFormatter(logging.Formatter):
    """Make each application log record independently parseable JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in ("event", "path", "method", "status", "duration_ms", "cost_usd"):
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        return json.dumps(payload, ensure_ascii=False, default=str)


logger = logging.getLogger("agent")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("application_started", extra={"event": "startup"})
    try:
        yield
    finally:
        # Uvicorn handles SIGTERM and waits for active requests before this runs.
        logger.info("application_stopped", extra={"event": "shutdown"})


app = FastAPI(title="Production AI Agent", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    user_id: str | None = Field(default=None, max_length=256)


@app.middleware("http")
async def log_request(request: Request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_failed",
            extra={
                "event": "request",
                "path": request.url.path,
                "method": request.method,
                "status": 500,
            },
        )
        raise
    logger.info(
        "request_complete",
        extra={
            "event": "request",
            "path": request.url.path,
            "method": request.method,
            "status": response.status_code,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    )
    return response


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness stays healthy even while Redis is unavailable."""
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    """Readiness requires Redis because protected requests depend on it."""
    if not redis_healthy():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis unavailable")
    return {"status": "ready"}


@app.post("/ask")
def ask(body: AskRequest, api_key: str = Depends(verify_api_key)) -> dict[str, str]:
    check_rate_limit(api_key)
    check_budget()
    answer = llm_ask(body.question)
    cost = record_cost(max(1, len(body.question.split())), max(1, len(answer.split())))
    logger.info("llm_request_complete", extra={"event": "llm", "cost_usd": cost})
    return {"question": body.question, "answer": answer}

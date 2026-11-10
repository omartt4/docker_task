"""Redis-backed response cache and request history."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import redis


DEFAULT_REDIS_URL = "redis://localhost:6379/0"
RESPONSE_CACHE_TTL_SECONDS = 3600
REQUEST_HISTORY_KEY = "api:request-history"


def _client() -> redis.Redis:
    return redis.Redis.from_url(
        os.getenv("REDIS_URL", DEFAULT_REDIS_URL),
        decode_responses=True,
        socket_connect_timeout=5,
    )


def _cache_key(prompt: str, model: str) -> str:
    digest = hashlib.sha256(f"{model}:{prompt}".encode("utf-8")).hexdigest()
    return f"api:generate:{digest}"


def get_cached_response(prompt: str, model: str) -> str | None:
    """Return a cached response, if one exists."""
    return _client().get(_cache_key(prompt, model))


def cache_response(prompt: str, model: str, response: str) -> None:
    """Cache a generated response for one hour."""
    _client().setex(
        _cache_key(prompt, model),
        RESPONSE_CACHE_TTL_SECONDS,
        response,
    )


def record_request(prompt: str, model: str, response: str, cached: bool) -> None:
    """Store request metadata and response in Redis history."""
    record = {
        "id": str(uuid4()),
        "prompt": prompt,
        "model": model,
        "response": response,
        "cached": cached,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    client = _client()
    client.lpush(REQUEST_HISTORY_KEY, json.dumps(record))
    client.ltrim(REQUEST_HISTORY_KEY, 0, 99)


def recent_requests(limit: int = 20) -> list[dict[str, object]]:
    """Return the most recent Redis-backed API requests."""
    records = _client().lrange(REQUEST_HISTORY_KEY, 0, limit - 1)
    return [json.loads(record) for record in records]

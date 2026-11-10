"""HTTP API entrypoint."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
import psycopg
from redis.exceptions import RedisError

from app.logging_config import configure_logging
from app.database import check_database_connection, initialize_database, save_generation
from app.ollama import generate_response
from app.redis_store import (
    cache_response,
    get_cached_response,
    recent_requests,
    record_request,
)


configure_logging()
logger = logging.getLogger(__name__)


class ItemCreate(BaseModel):
    """Payload accepted by the item creation endpoint."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100, description="Item name")
    quantity: int = Field(gt=0, le=10_000, description="Number of items")


class Item(ItemCreate):
    """Item returned by the API."""

    id: int


class GenerateRequest(BaseModel):
    """Prompt accepted by the Ollama generation endpoint."""

    model_config = ConfigDict(str_strip_whitespace=True)

    prompt: str = Field(min_length=1, max_length=4_000)


class GenerateResponse(BaseModel):
    """Generated response returned by the API."""

    model: str
    response: str


class RequestRecord(BaseModel):
    """A request and response stored in Redis history."""

    id: str
    prompt: str
    model: str
    response: str
    cached: bool
    created_at: str


items: list[Item] = []


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        initialize_database()
    except psycopg.Error as exc:
        logger.error("Database initialization failed: %s", exc)
        raise
    logger.info("API started")
    yield
    logger.info("API stopped")


app = FastAPI(
    title="FastAPI Logging Demo",
    version="0.1.0",
    description="A small API demonstrating validation and application logging.",
    lifespan=lifespan,
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Report service availability."""
    logger.info("Health check requested")
    return {"status": "ok"}


@app.get("/db/health", tags=["system"])
def database_health() -> dict[str, str]:
    """Check that the configured PostgreSQL database accepts queries."""
    try:
        if not check_database_connection():
            raise RuntimeError("Database health query returned an unexpected result")
    except (ConnectionError, psycopg.Error, RuntimeError) as exc:
        logger.error("Database health check failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    logger.info("Database health check passed")
    return {"status": "ok", "database": "postgresql"}


@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED, tags=["items"])
def create_item(payload: ItemCreate) -> Item:
    """Create an item after Pydantic validates its fields."""
    item = Item(id=len(items) + 1, **payload.model_dump())
    items.append(item)
    logger.info("Created item id=%s name=%s quantity=%s", item.id, item.name, item.quantity)
    return item


@app.post("/generate", response_model=GenerateResponse, tags=["generation"])
async def generate(payload: GenerateRequest) -> GenerateResponse:
    """Generate text with caching and Redis-backed request history."""
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5")
    try:
        response = get_cached_response(payload.prompt, model)
        if response is not None:
            record_request(payload.prompt, model, response, cached=True)
            logger.info("Returned cached response with model=%s", model)
            return GenerateResponse(model=model, response=response)
    except RedisError as exc:
        logger.error("Redis cache lookup failed: %s", exc)
        raise HTTPException(status_code=503, detail="Redis unavailable") from exc

    try:
        response = await generate_response(payload.prompt)
    except ConnectionError as exc:
        logger.error("Ollama connection failed: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error("Ollama generation failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        save_generation(payload.prompt, model, response)
    except psycopg.Error as exc:
        logger.error("Failed to save generation: %s", exc)
        raise HTTPException(status_code=503, detail="Could not save response") from exc
    try:
        cache_response(payload.prompt, model, response)
        record_request(payload.prompt, model, response, cached=False)
    except RedisError as exc:
        logger.error("Redis response storage failed: %s", exc)
        raise HTTPException(status_code=503, detail="Redis unavailable") from exc
    logger.info("Generated response with model=%s", model)
    return GenerateResponse(model=model, response=response)


@app.get("/requests/recent", response_model=list[RequestRecord], tags=["system"])
def get_recent_requests(limit: int = 20) -> list[RequestRecord]:
    """Return recent generation requests stored in Redis."""
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    try:
        return [RequestRecord.model_validate(record) for record in recent_requests(limit)]
    except RedisError as exc:
        logger.error("Redis request history lookup failed: %s", exc)
        raise HTTPException(status_code=503, detail="Redis unavailable") from exc

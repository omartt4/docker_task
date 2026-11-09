"""HTTP API entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from pydantic import BaseModel, ConfigDict, Field

from app.logging_config import configure_logging


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


items: list[Item] = []


@asynccontextmanager
async def lifespan(_: FastAPI):
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


@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED, tags=["items"])
def create_item(payload: ItemCreate) -> Item:
    """Create an item after Pydantic validates its fields."""
    item = Item(id=len(items) + 1, **payload.model_dump())
    items.append(item)
    logger.info("Created item id=%s name=%s quantity=%s", item.id, item.name, item.quantity)
    return item

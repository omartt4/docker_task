"""PostgreSQL connection helpers."""

from __future__ import annotations

import os

import psycopg


DEFAULT_DATABASE_URL = "postgresql://omar:123456@localhost:8000/mydatabase"


def initialize_database() -> None:
    """Create application tables when they do not already exist."""
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    with psycopg.connect(database_url, connect_timeout=5) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS generations (
                id BIGSERIAL PRIMARY KEY,
                prompt TEXT NOT NULL,
                model TEXT NOT NULL,
                response TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def save_generation(prompt: str, model: str, response: str) -> None:
    """Persist a successful Ollama generation."""
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    with psycopg.connect(database_url, connect_timeout=5) as connection:
        connection.execute(
            "INSERT INTO generations (prompt, model, response) VALUES (%s, %s, %s)",
            (prompt, model, response),
        )
        connection.commit()


def check_database_connection() -> bool:
    """Open a PostgreSQL connection and run a lightweight query."""
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    with psycopg.connect(database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return cursor.fetchone() == (1,)

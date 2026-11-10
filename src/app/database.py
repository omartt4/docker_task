"""PostgreSQL connection helpers."""

from __future__ import annotations

import os

import psycopg


DEFAULT_DATABASE_URL = "postgresql://omar:123456@localhost:8000/mydatabase"


def check_database_connection() -> bool:
    """Open a PostgreSQL connection and run a lightweight query."""
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    with psycopg.connect(database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return cursor.fetchone() == (1,)

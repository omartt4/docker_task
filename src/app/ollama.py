"""Client for the local Ollama generation API."""

from __future__ import annotations

import os

import httpx


DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:1.5"


async def generate_response(prompt: str) -> str:
    """Generate a response using the configured Ollama model."""
    base_url = os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL).rstrip("/")
    model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"Ollama returned HTTP {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise ConnectionError("Could not connect to Ollama") from exc

    data = response.json()
    generated = data.get("response")
    if not isinstance(generated, str) or not generated.strip():
        raise RuntimeError("Ollama returned no generated response")
    return generated

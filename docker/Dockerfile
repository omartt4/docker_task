FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    LOG_FILE=/app/logs/app.log \
    DATABASE_URL=postgresql://omar@host.docker.internal:8000/mydatabase \
    REDIS_URL=redis://host.docker.internal:6379/0 \
    OLLAMA_BASE_URL=http://host.docker.internal:11434 \
    OLLAMA_MODEL=qwen2.5:1.5b

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

COPY src ./src
RUN mkdir -p /app/logs

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

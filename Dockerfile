FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    LOG_FILE=/app/logs/app.log

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

COPY src ./src
RUN mkdir -p /app/logs

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

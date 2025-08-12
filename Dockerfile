# Simple single-stage image using uv to install and run
FROM ghcr.io/astral-sh/uv:0.6.9-python3.11-bookworm

WORKDIR /app

# Copy project metadata first for better layer caching
COPY pyproject.toml ./

# Sync dependencies (will create .venv)
RUN uv sync --no-dev

# Copy application source
COPY app ./app

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PORT=8080

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

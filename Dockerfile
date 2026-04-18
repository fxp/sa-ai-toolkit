FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install Python dependencies first (cache-friendly)
COPY server/requirements.txt /app/server/requirements.txt
RUN pip install --no-cache-dir -r /app/server/requirements.txt

# Copy demo packages (per-demo core.py + cli.py) and server + docs
COPY api /app/api
COPY demos /app/demos
COPY docs /app/docs
COPY server /app/server

# Remove submodule content that shouldn't ship (heavy MiroFish backend, etc.)
RUN find /app/demos -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]

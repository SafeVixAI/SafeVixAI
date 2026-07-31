# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
# ────────────────────────────────────────────────────────────────
# Backend — FastAPI + PostGIS (multi-stage build)
# DEVOPS#9 FIX: Converted from single-stage to multi-stage per audit
# ────────────────────────────────────────────────────────────────

# Stage 1: Builder — install build deps and compile wheels
FROM python:3.11.9-slim-bookworm@sha256:2856e6af199e8128161abd320575eb9b341f3b76f017b5d0c9cd364f60d8a050 AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-render.txt ./requirements-render.txt
RUN pip install --upgrade pip && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements-render.txt

# Stage 2: Runner — copy only wheels and app code
FROM python:3.11.9-slim-bookworm@sha256:2856e6af199e8128161abd320575eb9b341f3b76f017b5d0c9cd364f60d8a050 AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Copy compiled wheels from builder
COPY --from=builder /wheels /wheels
COPY requirements-render.txt ./requirements-render.txt
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

COPY . .

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

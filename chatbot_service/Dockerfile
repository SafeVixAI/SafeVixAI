# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
# ── Stage 1: Build dependencies ──────────────────────────────────────────────
FROM python:3.11.9-slim-bookworm AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system deps needed for pdfplumber / chromadb
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-render.txt .
RUN pip install --prefix=/install -r requirements-render.txt

# ── Stage 2: Runtime image ────────────────────────────────────────────────────
FROM python:3.11.9-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Runtime libs only
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Non-root user
RUN useradd -m -u 1000 appuser && mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser

# Copy application code
COPY --chown=appuser:appuser . .

# Build RAG vectorstore index at container startup (if not pre-built)
# Comment this out if you mount a pre-built chroma_db volume
# RUN python data/build_vectorstore.py

EXPOSE 8010

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8010/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]

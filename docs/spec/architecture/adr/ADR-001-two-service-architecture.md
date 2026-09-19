# ADR-001: Two-Service Architecture

**Date:** 2026-05-19  
**Status:** ✅ Accepted  
**Author:** SafeVixAI Engineering  

## Context

The application requires two distinct workloads:
1. A lightweight REST API for CRUD operations, geospatial queries, and real-time tracking
2. An AI-powered chatbot with heavy ML dependencies (torch, transformers, ~2GB)

Deploying them as a single service would create unnecessary coupling and bloat the production image.

## Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Single monolith** | One FastAPI app serving both workloads | Simple deployment, shared DB sessions | 2GB+ image size, coupled deploys |
| **Two services (chosen)** | Separate FastAPI apps with different dependencies | Independent scaling, focused images, separate test suites | Extra network hop, shared secrets management |
| **Microservices** | Many small services | Maximum isolation | Over-engineered for current scope |

## Decision

Deploy as two separate FastAPI services:
- **Backend** (`:8000`): FastAPI + SQLAlchemy + PostGIS
- **Chatbot** (`:8010`): FastAPI + ChromaDB + LLM providers

Service-to-service auth via `X-Internal-Api-Key` header.

## Consequences

- Backend image stays ~200MB, chatbot image ~4GB
- Each service can scale independently (2-6 backend, 1-3 chatbot instances)
- Developers must run two `uvicorn` processes locally
- Docker Compose orchestrates both services in development

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Global enterprise exception gateways for SafeVixAI Backend.

Catches unhandled domain and database errors and formats them into standard JSON wrappers.
"""
from __future__ import annotations

import logging
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class DomainError(Exception):
    """Base exception for domain logic failures."""
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ResourceNotFoundError(DomainError):
    """Raised when a requested domain entity does not exist."""
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=404)


class InvalidTransitionError(DomainError):
    """Raised during an invalid state machine transition."""
    def __init__(self, message: str = "Invalid state transition") -> None:
        super().__init__(message, status_code=409)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        logger.warning("Domain error on %s: %s", request.url.path, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.__class__.__name__, "message": exc.message}},
        )

    try:
        from sqlalchemy.exc import IntegrityError
        @app.exception_handler(IntegrityError)
        async def sqlalchemy_integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
            logger.error("Database integrity error on %s: %s", request.url.path, str(exc))
            return JSONResponse(
                status_code=409,
                content={"error": {"code": "DatabaseIntegrityError", "message": "A conflict occurred with existing database records."}},
            )
    except ImportError:
        pass

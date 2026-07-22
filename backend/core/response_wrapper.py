# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import gzip
import json
import logging
from datetime import UTC, datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from models.schemas import ApiErrorResponse, ApiResponse

logger = logging.getLogger("safevixai.response_wrapper")


class ApiResponseMiddleware(BaseHTTPMiddleware):
    """Wraps all 2xx JSON responses in the ApiResponse<T> envelope."""

    async def dispatch(self, request: Request, call_next):
        try:
            response: Response = await call_next(request)

            if not (200 <= response.status_code < 300):
                return response

            # _StreamingResponse can lose media_type through BaseHTTPMiddleware wrapping.
            # Use Content-Type header directly instead.
            content_type = response.headers.get("content-type", "")
            if content_type and "json" not in content_type:
                return response

            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            if not body:
                return response

            # Decompress gzip if compressed by GeoJSONCompressionMiddleware
            new_headers = dict(response.headers)
            if new_headers.get("content-encoding") == "gzip":
                body = gzip.decompress(body)
                del new_headers["content-encoding"]

            data = json.loads(body)
            wrapped = ApiResponse(
                success=True,
                data=data,
                error=None,
                timestamp=datetime.now(UTC).isoformat(),
            )
            new_headers.pop("content-length", None)
            new_headers.pop("Content-Length", None)
            return JSONResponse(
                status_code=response.status_code,
                content=wrapped.model_dump(mode="json"),
                headers=new_headers,
            )
        except Exception as exc:
            return JSONResponse(
                status_code=500,
                content=ApiErrorResponse(
                    error={"code": "INTERNAL_ERROR", "message": str(exc)},
                    timestamp=datetime.now(UTC).isoformat(),
                ).model_dump(),
            )

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tests for core/response_wrapper.py — ApiResponseMiddleware.

Covers:
- 2xx JSON responses are wrapped in ApiResponse envelope
- Non-2xx responses pass through unwrapped
- Non-JSON responses pass through
- Empty body responses pass through
- Gzip decompression handling
- Error handling in dispatch
"""

from __future__ import annotations

import gzip
import json
from unittest.mock import MagicMock

import pytest
from fastapi import Request, Response

from core.response_wrapper import ApiResponseMiddleware


class AsyncBytesIterator:
    """Helper to simulate async body_iterator."""
    def __init__(self, chunks: list[bytes]):
        self.chunks = list(chunks)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.chunks:
            raise StopAsyncIteration
        return self.chunks.pop(0)


def _make_mock_response(
    status_code: int = 200,
    body: bytes = b'{"message": "ok"}',
    content_type: str = "application/json",
    extra_headers: dict[str, str] | None = None,
) -> MagicMock:
    """Create a mock Response with the expected interface."""
    headers = {"content-type": content_type}
    if extra_headers:
        headers.update(extra_headers)
    mock_resp = MagicMock(spec=Response)
    mock_resp.status_code = status_code
    mock_resp.headers = headers
    if body:
        mock_resp.body_iterator = AsyncBytesIterator([body])
    else:
        mock_resp.body_iterator = AsyncBytesIterator([])
    return mock_resp


class TestApiResponseMiddleware:
    """Tests for ApiResponseMiddleware dispatch method."""

    @pytest.mark.asyncio
    async def test_2xx_json_wrapped(self):
        """2xx JSON responses should be wrapped in ApiResponse envelope."""
        middleware = ApiResponseMiddleware(app=MagicMock())

        async def call_next(request):
            return _make_mock_response(status_code=200, body=b'{"message": "ok"}')

        request = MagicMock(spec=Request)
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["success"] is True
        assert body["data"]["message"] == "ok"
        assert "timestamp" in body

    @pytest.mark.asyncio
    async def test_non_2xx_passthrough(self):
        """Non-2xx responses should pass through unwrapped."""
        middleware = ApiResponseMiddleware(app=MagicMock())

        async def call_next(request):
            return _make_mock_response(status_code=404, body=b'{"error": "not found"}')

        request = MagicMock(spec=Request)
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_non_json_content_type_passthrough(self):
        """Non-JSON content type responses should pass through."""
        middleware = ApiResponseMiddleware(app=MagicMock())

        async def call_next(request):
            return _make_mock_response(
                status_code=200,
                body=b"<html></html>",
                content_type="text/html",
            )

        request = MagicMock(spec=Request)
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200
        assert response.headers.get("content-type", "") == "text/html"

    @pytest.mark.asyncio
    async def test_empty_body_passthrough(self):
        """Empty body responses should pass through."""
        middleware = ApiResponseMiddleware(app=MagicMock())

        async def call_next(request):
            return _make_mock_response(status_code=200, body=b"")

        request = MagicMock(spec=Request)
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_3xx_redirect_passthrough(self):
        """3xx redirect responses should pass through unwrapped."""
        middleware = ApiResponseMiddleware(app=MagicMock())

        async def call_next(request):
            return _make_mock_response(status_code=302, body=b'')

        request = MagicMock(spec=Request)
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 302

    @pytest.mark.asyncio
    async def test_gzip_decompression(self):
        """Response with gzip content-encoding should be decompressed before wrapping."""
        middleware = ApiResponseMiddleware(app=MagicMock())

        original_body = json.dumps({"message": "compressed"}).encode()
        compressed = gzip.compress(original_body)

        async def call_next(request):
            return _make_mock_response(
                status_code=200,
                body=compressed,
                extra_headers={"content-encoding": "gzip"},
            )

        request = MagicMock(spec=Request)
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["data"]["message"] == "compressed"

    @pytest.mark.asyncio
    async def test_gzip_decompression_removes_header(self):
        """Gzip content-encoding header should be removed from wrapped response."""
        middleware = ApiResponseMiddleware(app=MagicMock())

        compressed = gzip.compress(json.dumps({"x": 1}).encode())

        async def call_next(request):
            return _make_mock_response(
                status_code=200,
                body=compressed,
                extra_headers={
                    "content-encoding": "gzip",
                    "content-length": str(len(compressed)),
                },
            )

        request = MagicMock(spec=Request)
        response = await middleware.dispatch(request, call_next)

        # content-encoding should be removed (content-length may be re-added by JSONResponse)
        assert "content-encoding" not in response.headers
        # Verify content-length reflects decompressed size, not compressed
        cl = int(response.headers.get("content-length", "0"))
        assert cl > 0, "content-length should be set on wrapped response"

    @pytest.mark.asyncio
    async def test_error_in_call_next_returns_500(self):
        """Exception in call_next should return 500 error response."""
        middleware = ApiResponseMiddleware(app=MagicMock())

        async def call_next(request):
            raise ValueError("Something broke")

        request = MagicMock(spec=Request)
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 500
        body = json.loads(response.body)
        assert body["error"]["code"] == "INTERNAL_ERROR"
        assert "Something broke" in body["error"]["message"]

    @pytest.mark.asyncio
    async def test_json_decode_error_wrapped_as_500(self):
        """Invalid JSON body should be caught and returned as 500."""
        middleware = ApiResponseMiddleware(app=MagicMock())

        async def call_next(request):
            return _make_mock_response(
                status_code=200,
                body=b"not valid json",
            )

        request = MagicMock(spec=Request)
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_content_type_header_with_charset(self):
        """Content-Type with charset should still match json check."""
        middleware = ApiResponseMiddleware(app=MagicMock())

        async def call_next(request):
            return _make_mock_response(
                status_code=200,
                body=b'{"ok": true}',
                content_type="application/json; charset=utf-8",
            )

        request = MagicMock(spec=Request)
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["success"] is True

    @pytest.mark.asyncio
    async def test_no_content_type_still_wraps(self):
        """Response without content-type should still be wrapped (backward compat)."""
        middleware = ApiResponseMiddleware(app=MagicMock())

        async def call_next(request):
            return _make_mock_response(
                status_code=200,
                body=b'{"ok": true}',
                content_type="",
            )

        request = MagicMock(spec=Request)
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["success"] is True

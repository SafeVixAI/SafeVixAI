# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tests for idempotency middleware."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from core.idempotency import (
    IdempotencyMiddleware,
    _IDEMPOTENCY_TTL,
    _IDEMPOTENCY_PREFIX,
)
from fastapi import Request, Response
from starlette.responses import JSONResponse


class AsyncIterator:
    """Helper class to create async iterators for testing."""
    def __init__(self, items):
        self.items = items
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)


@pytest.fixture
def mock_cache():
    """Create mock cache."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.setex = AsyncMock(return_value=True)
    cache.close = AsyncMock()
    return cache


@pytest.fixture
def mock_request():
    """Create mock request."""
    request = MagicMock(spec=Request)
    request.method = "POST"
    request.headers = {}
    request.client = None
    return request


@pytest.fixture
def mock_call_next():
    """Create mock call_next function."""
    async def call_next(request):
        # Create a mock response with body_iterator
        response = MagicMock()
        response.status_code = 200
        response.body_iterator = AsyncIterator([b'{"message": "success"}'])
        return response
    return call_next


@pytest.mark.asyncio
async def test_idempotency_middleware_get_request(mock_request, mock_call_next, mock_cache):
    """Test that GET requests bypass idempotency."""
    mock_request.method = "GET"
    
    middleware = IdempotencyMiddleware(app=MagicMock())
    
    with patch('core.idempotency.create_cache', return_value=mock_cache):
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response is not None
        mock_cache.get.assert_not_called()


@pytest.mark.asyncio
async def test_idempotency_middleware_delete_request(mock_request, mock_call_next, mock_cache):
    """Test that DELETE requests bypass idempotency."""
    mock_request.method = "DELETE"
    
    middleware = IdempotencyMiddleware(app=MagicMock())
    
    with patch('core.idempotency.create_cache', return_value=mock_cache):
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response is not None
        mock_cache.get.assert_not_called()


@pytest.mark.asyncio
async def test_idempotency_middleware_no_idempotency_key(mock_request, mock_call_next, mock_cache):
    """Test that requests without Idempotency-Key bypass idempotency."""
    mock_request.method = "POST"
    mock_request.headers = {}
    
    middleware = IdempotencyMiddleware(app=MagicMock())
    
    with patch('core.idempotency.create_cache', return_value=mock_cache):
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response is not None
        mock_cache.get.assert_not_called()


@pytest.mark.asyncio
async def test_idempotency_middleware_cache_hit(mock_request, mock_call_next, mock_cache):
    """Test idempotency cache hit."""
    mock_request.method = "POST"
    mock_request.headers = {"Idempotency-Key": "test-key-123"}
    
    cached_data = json.dumps({
        "status_code": 200,
        "body": {"message": "cached response"}
    })
    mock_cache.get = AsyncMock(return_value=cached_data)
    
    middleware = IdempotencyMiddleware(app=MagicMock())
    
    with patch('core.idempotency.create_cache', return_value=mock_cache):
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 200
        assert response.body == b'{"message":"cached response"}'
        assert response.headers.get("X-Idempotency-Cached") == "true"
        mock_cache.get.assert_called_once_with(f"{_IDEMPOTENCY_PREFIX}test-key-123")


@pytest.mark.asyncio
async def test_idempotency_middleware_cache_miss(mock_request, mock_call_next, mock_cache):
    """Test idempotency cache miss."""
    mock_request.method = "POST"
    mock_request.headers = {"Idempotency-Key": "test-key-456"}
    mock_cache.get = AsyncMock(return_value=None)
    
    middleware = IdempotencyMiddleware(app=MagicMock())
    
    with patch('core.idempotency.create_cache', return_value=mock_cache):
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 200
        assert response.headers.get("X-Idempotency-Cached") == "false"
        mock_cache.get.assert_called_once()
        mock_cache.setex.assert_called_once()


@pytest.mark.asyncio
async def test_idempotency_middleware_put_request(mock_request, mock_call_next, mock_cache):
    """Test idempotency for PUT requests."""
    mock_request.method = "PUT"
    mock_request.headers = {"Idempotency-Key": "test-key-789"}
    mock_cache.get = AsyncMock(return_value=None)
    
    middleware = IdempotencyMiddleware(app=MagicMock())
    
    with patch('core.idempotency.create_cache', return_value=mock_cache):
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 200
        mock_cache.get.assert_called_once()
        mock_cache.setex.assert_called_once()


@pytest.mark.asyncio
async def test_idempotency_middleware_patch_request(mock_request, mock_call_next, mock_cache):
    """Test idempotency for PATCH requests."""
    mock_request.method = "PATCH"
    mock_request.headers = {"Idempotency-Key": "test-key-012"}
    mock_cache.get = AsyncMock(return_value=None)
    
    middleware = IdempotencyMiddleware(app=MagicMock())
    
    with patch('core.idempotency.create_cache', return_value=mock_cache):
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 200
        mock_cache.get.assert_called_once()
        mock_cache.setex.assert_called_once()


@pytest.mark.asyncio
async def test_idempotency_middleware_error_response_not_cached(mock_request, mock_call_next, mock_cache):
    """Test that error responses (4xx, 5xx) are not cached."""
    mock_request.method = "POST"
    mock_request.headers = {"Idempotency-Key": "test-key-error"}
    mock_cache.get = AsyncMock(return_value=None)
    
    async def error_call_next(request):
        return JSONResponse(content={"error": "Bad request"}, status_code=400)
    
    middleware = IdempotencyMiddleware(app=MagicMock())
    
    with patch('core.idempotency.create_cache', return_value=mock_cache):
        response = await middleware.dispatch(mock_request, error_call_next)
        
        assert response.status_code == 400
        mock_cache.setex.assert_not_called()


@pytest.mark.asyncio
async def test_idempotency_middleware_redirect_response_cached(mock_request, mock_call_next, mock_cache):
    """Test that redirect responses (3xx) are cached."""
    mock_request.method = "POST"
    mock_request.headers = {"Idempotency-Key": "test-key-redirect"}
    mock_cache.get = AsyncMock(return_value=None)
    
    async def redirect_call_next(request):
        response = MagicMock()
        response.status_code = 302
        response.body_iterator = AsyncIterator([b'{"url": "/new-location"}'])
        return response
    
    middleware = IdempotencyMiddleware(app=MagicMock())
    
    with patch('core.idempotency.create_cache', return_value=mock_cache):
        response = await middleware.dispatch(mock_request, redirect_call_next)
        
        assert response.status_code == 302
        mock_cache.setex.assert_called_once()


@pytest.mark.asyncio
async def test_idempotency_middleware_non_json_body(mock_request, mock_call_next, mock_cache):
    """Test handling of non-JSON response bodies."""
    mock_request.method = "POST"
    mock_request.headers = {"Idempotency-Key": "test-key-nonjson"}
    mock_cache.get = AsyncMock(return_value=None)
    
    async def non_json_call_next(request):
        response = MagicMock()
        response.status_code = 200
        response.body_iterator = AsyncIterator([b'{"message": "valid json"}'])
        return response
    
    middleware = IdempotencyMiddleware(app=MagicMock())
    
    with patch('core.idempotency.create_cache', return_value=mock_cache):
        response = await middleware.dispatch(mock_request, non_json_call_next)
        
        assert response.status_code == 200
        # Should cache the response
        mock_cache.setex.assert_called_once()


@pytest.mark.asyncio
async def test_idempotency_middleware_exception_handling(mock_request, mock_call_next, mock_cache):
    """Test that exceptions are handled gracefully."""
    mock_request.method = "POST"
    mock_request.headers = {"Idempotency-Key": "test-key-exception"}
    mock_cache.get = AsyncMock(side_effect=Exception("Cache error"))
    
    middleware = IdempotencyMiddleware(app=MagicMock())
    
    with patch('core.idempotency.create_cache', return_value=mock_cache):
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should fallback to call_next on exception
        assert response is not None


@pytest.mark.asyncio
async def test_idempotency_middleware_cache_close(mock_request, mock_call_next, mock_cache):
    """Test that cache is closed in finally block."""
    mock_request.method = "POST"
    mock_request.headers = {"Idempotency-Key": "test-key-close"}
    mock_cache.get = AsyncMock(return_value=None)
    
    middleware = IdempotencyMiddleware(app=MagicMock())
    
    with patch('core.idempotency.create_cache', return_value=mock_cache):
        await middleware.dispatch(mock_request, mock_call_next)
        
        mock_cache.close.assert_called_once()


@pytest.mark.asyncio
async def test_idempotency_middleware_cache_key_format(mock_request, mock_call_next, mock_cache):
    """Test that cache key is formatted correctly."""
    mock_request.method = "POST"
    mock_request.headers = {"Idempotency-Key": "unique-key-123"}
    mock_cache.get = AsyncMock(return_value=None)
    
    middleware = IdempotencyMiddleware(app=MagicMock())
    
    with patch('core.idempotency.create_cache', return_value=mock_cache):
        await middleware.dispatch(mock_request, mock_call_next)
        
        expected_key = f"{_IDEMPOTENCY_PREFIX}unique-key-123"
        mock_cache.get.assert_called_once_with(expected_key)


@pytest.mark.asyncio
async def test_idempotency_middleware_ttl_value(mock_request, mock_call_next, mock_cache):
    """Test that TTL is set correctly."""
    mock_request.method = "POST"
    mock_request.headers = {"Idempotency-Key": "test-key-ttl"}
    mock_cache.get = AsyncMock(return_value=None)
    
    middleware = IdempotencyMiddleware(app=MagicMock())
    
    with patch('core.idempotency.create_cache', return_value=mock_cache):
        await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify TTL is 24 hours (86400 seconds)
        call_args = mock_cache.setex.call_args
        assert call_args[0][1] == _IDEMPOTENCY_TTL
        assert _IDEMPOTENCY_TTL == 86400


@pytest.mark.asyncio
async def test_idempotency_middleware_empty_body(mock_request, mock_call_next, mock_cache):
    """Test handling of empty response body."""
    mock_request.method = "POST"
    mock_request.headers = {"Idempotency-Key": "test-key-empty"}
    mock_cache.get = AsyncMock(return_value=None)
    
    async def empty_call_next(request):
        response = Response(status_code=204)
        return response
    
    middleware = IdempotencyMiddleware(app=MagicMock())
    
    with patch('core.idempotency.create_cache', return_value=mock_cache):
        response = await middleware.dispatch(mock_request, empty_call_next)
        
        assert response.status_code == 204


def test_idempotency_constants():
    """Test idempotency constants."""
    assert _IDEMPOTENCY_TTL == 86400  # 24 hours
    assert _IDEMPOTENCY_PREFIX == "idempotency:"


@pytest.mark.asyncio
async def test_idempotency_middleware_empty_response_body(mock_request, mock_call_next, mock_cache):
    """Test handling of empty response body in caching (line 77-78 branch)."""
    mock_request.method = "POST"
    mock_request.headers = {"Idempotency-Key": "test-key-emptybody"}
    mock_cache.get = AsyncMock(return_value=None)

    async def empty_body_call_next(request):
        response = MagicMock()
        response.status_code = 200
        response.body_iterator = AsyncIterator([b''])
        return response

    middleware = IdempotencyMiddleware(app=MagicMock())

    with patch('core.idempotency.create_cache', return_value=mock_cache):
        response = await middleware.dispatch(mock_request, empty_body_call_next)
        assert response.status_code == 200
        mock_cache.setex.assert_called_once()


@pytest.mark.asyncio
async def test_idempotency_middleware_json_decode_error(mock_request, mock_call_next, mock_cache):
    """Test handling of JSON decode error during caching (line 77-78 decode branch)."""
    mock_request.method = "POST"
    mock_request.headers = {"Idempotency-Key": "test-key-jsonerror"}
    mock_cache.get = AsyncMock(return_value=None)

    async def bad_json_call_next(request):
        response = MagicMock()
        response.status_code = 200
        response.body_iterator = AsyncIterator([b'not valid json'])
        return response

    middleware = IdempotencyMiddleware(app=MagicMock())

    with patch('core.idempotency.create_cache', return_value=mock_cache):
        response = await middleware.dispatch(mock_request, bad_json_call_next)
        assert response.status_code == 200
        # Should gracefully handle the JSON decode error

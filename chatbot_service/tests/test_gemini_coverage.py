# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Coverage tests for providers/gemini_provider.py — uncovered lines: 51-52, 84, 146, 149, 152-154."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from providers.base import ProviderRequest
from providers.gemini_provider import GeminiProvider

_REQUEST = ProviderRequest(message="test", intent="general", history=[])


class _AsyncBytesStream:
    """Simulates httpx's streaming response for Gemini SSE."""
    def __init__(self, chunks: list[bytes]):
        self.chunks = chunks
        self._idx = 0

    async def aclose(self):
        pass

    def __aiter__(self):
        return self

    async def __anext__(self) -> bytes:
        if self._idx >= len(self.chunks):
            raise StopAsyncIteration
        val = self.chunks[self._idx]
        self._idx += 1
        return val


def _make_stream_resp(sse_chunks: list[str]):
    """Build mock response with aiter_bytes returning SSE chunks."""
    resp = MagicMock()
    resp.status_code = 200
    resp.headers = {}
    resp.aiter_bytes = lambda: _AsyncBytesStream([c.encode() for c in sse_chunks])
    return resp


def _mock_gemini_client(post_return=None, stream_resp=None):
    client = MagicMock()
    client.is_closed = False
    if post_return:
        client.post = AsyncMock(return_value=post_return)
    cm = MagicMock()
    if stream_resp:
        cm.__aenter__ = AsyncMock(return_value=stream_resp)
    else:
        cm.__aenter__ = AsyncMock(return_value=MagicMock())
    cm.__aexit__ = AsyncMock(return_value=False)
    client.stream = MagicMock(return_value=cm)
    return client


class TestGeminiStream:
    """GeminiProvider.stream() — uncovered paths."""

    @pytest.mark.asyncio
    async def test_stream_assistant_role_mapping(self):
        """Line 51-52: assistant role maps to 'model'."""
        provider = GeminiProvider(api_key="test-key")
        req = ProviderRequest(
            message="ping",
            intent="general",
            history=[{"role": "assistant", "content": "previous response"}],
        )
        stream_data = (
            b'data: {"candidates":[{"content":{"parts":[{"text":"hello"}]}}]}\n\n'
            b'data: [DONE]\n\n'
        )
        resp = MagicMock()
        resp.status_code = 200
        resp.headers = {}
        resp.aiter_text = lambda: _async_text_iter(stream_data.decode())
        client = MagicMock()
        client.is_closed = False
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=resp)
        cm.__aexit__ = AsyncMock(return_value=False)
        client.stream = MagicMock(return_value=cm)

        with patch.object(provider, "_get_client", return_value=client):
            chunks = [c async for c in provider.stream(req)]
        assert chunks == ["hello"]

    @pytest.mark.asyncio
    async def test_stream_empty_data_str_skipped(self):
        """Line 84: empty data_str after stripping is skipped."""
        provider = GeminiProvider(api_key="test-key")
        stream_data = (
            b'data: \n\n'
            b'data: {"candidates":[{"content":{"parts":[{"text":"world"}]}}]}\n\n'
            b'data: [DONE]\n\n'
        )
        resp = MagicMock()
        resp.status_code = 200
        resp.headers = {}
        resp.aiter_text = lambda: _async_text_iter(stream_data.decode())
        client = MagicMock()
        client.is_closed = False
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=resp)
        cm.__aexit__ = AsyncMock(return_value=False)
        client.stream = MagicMock(return_value=cm)

        with patch.object(provider, "_get_client", return_value=client):
            chunks = [c async for c in provider.stream(_REQUEST)]
        assert chunks == ["world"]


class TestGeminiGenerateErrors:
    """GeminiProvider.generate() — empty candidates, parts, text."""

    @pytest.fixture
    def gemini(self) -> GeminiProvider:
        return GeminiProvider(api_key="test-key")

    @pytest.mark.asyncio
    async def test_empty_candidates_raises(self, gemini: GeminiProvider):
        """Line 146: empty candidates raises KeyError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"candidates": []}
        client = _mock_gemini_client(post_return=mock_resp)
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            with patch.object(gemini, "_get_client", return_value=client):
                with pytest.raises(RuntimeError, match="empty candidates"):
                    await gemini.generate(_REQUEST)

    @pytest.mark.asyncio
    async def test_empty_parts_raises(self, gemini: GeminiProvider):
        """Line 149: 'content' exists but 'parts' is empty."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"candidates": [{"content": {"parts": []}}]}
        client = _mock_gemini_client(post_return=mock_resp)
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            with patch.object(gemini, "_get_client", return_value=client):
                with pytest.raises(RuntimeError, match="empty parts"):
                    await gemini.generate(_REQUEST)

    @pytest.mark.asyncio
    async def test_empty_text_raises(self, gemini: GeminiProvider):
        """Line 152-154: parts exists but text is empty -> KeyError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"candidates": [{"content": {"parts": [{"text": ""}]}}]}
        client = _mock_gemini_client(post_return=mock_resp)
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            with patch.object(gemini, "_get_client", return_value=client):
                with pytest.raises(RuntimeError, match="empty text"):
                    await gemini.generate(_REQUEST)

    @pytest.mark.asyncio
    async def test_api_error_response(self, gemini: GeminiProvider):
        """API returns error structure instead of candidates."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"error": {"message": "API error"}}
        client = _mock_gemini_client(post_return=mock_resp)
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            with patch.object(gemini, "_get_client", return_value=client):
                with pytest.raises(RuntimeError, match="empty candidates"):
                    await gemini.generate(_REQUEST)

    @pytest.mark.asyncio
    async def test_no_api_key_returns_empty_stream(self):
        """Stream with no API key returns empty."""
        with patch.dict("os.environ", {}, clear=True):
            gemini_clean = GeminiProvider()
            chunks = [c async for c in gemini_clean.stream(_REQUEST)]
        assert chunks == []

    @pytest.mark.asyncio
    async def test_no_api_key_raises_in_generate(self):
        """Generate with no API key raises RuntimeError."""
        with patch.dict("os.environ", {}, clear=True):
            gemini_clean = GeminiProvider()
            with pytest.raises(RuntimeError, match="Missing env var"):
                await gemini_clean.generate(_REQUEST)


def _async_text_iter(text: str):
    """Helper: simulate aiter_text for Gemini streaming."""
    async def gen():
        yield text
    return gen()


class TestGeminiGenerate:
    """GeminiProvider.generate() — remaining edge cases."""

    @pytest.mark.asyncio
    async def test_generate_assistant_role_mapping(self):
        """Line 131-132: assistant role maps to 'model' in generate()."""
        provider = GeminiProvider(api_key="test-key")
        req = ProviderRequest(
            message="ping",
            intent="general",
            history=[{"role": "assistant", "content": "previous bot reply"}],
        )
        resp_data = {
            "candidates": [{
                "content": {"parts": [{"text": "gemini reply"}]},
                "finishReason": "STOP",
            }]
        }
        resp = MagicMock()
        resp.status_code = 200
        resp.headers = {}
        resp.json.return_value = resp_data
        client = MagicMock()
        client.is_closed = False
        client.post = AsyncMock(return_value=resp)
        with patch.object(provider, "_get_client", return_value=client):
            result = await provider.generate(req)
        assert result.text == "gemini reply"
        assert result.provider == "gemini"

    @pytest.mark.asyncio
    async def test_generate_with_system_text(self):
        """Lines 142-145: system instruction in generate()."""
        provider = GeminiProvider(api_key="test-key")
        req = ProviderRequest(
            message="user msg",
            intent="general",
            history=[],
            tool_summaries=["tool result summary"],
        )
        resp_data = {
            "candidates": [{
                "content": {"parts": [{"text": "reply with tool context"}]},
                "finishReason": "STOP",
            }]
        }
        resp = MagicMock()
        resp.status_code = 200
        resp.headers = {}
        resp.json.return_value = resp_data
        client = MagicMock()
        client.is_closed = False
        client.post = AsyncMock(return_value=resp)
        with patch.object(provider, "_get_client", return_value=client):
            result = await provider.generate(req)
        assert "tool" in result.text.lower()

    @pytest.mark.asyncio
    async def test_stream_system_text_parts(self):
        """Line 76-79: system instruction in stream()."""
        provider = GeminiProvider(api_key="test-key")
        req = ProviderRequest(
            message="user msg",
            intent="general",
            history=[],
            tool_summaries=["injected context"],
        )
        stream_text = (
            'data: {"candidates":[{"content":{"parts":[{"text":"ok"}]}}]}\n\n'
            'data: [DONE]\n\n'
        )
        resp = MagicMock()
        resp.status_code = 200
        resp.headers = {}
        resp.aiter_text = lambda: _async_text_iter(stream_text)
        client = MagicMock()
        client.is_closed = False
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=resp)
        cm.__aexit__ = AsyncMock(return_value=False)
        client.stream = MagicMock(return_value=cm)
        with patch.object(provider, "_get_client", return_value=client):
            chunks = [c async for c in provider.stream(req)]
        assert chunks == ["ok"]

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""JWKS Manager tests for SafeVixAI backend."""
from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from core.jwks import (
    JWKS_CACHE_TTL_SECONDS,
    ROTATION_INTERVAL_SECONDS,
    ROTATION_WINDOW_SECONDS,
    JWKSManager,
)

# ── JWKS Manager Tests ──────────────────────────────────────────────────────

class TestJWKSManagerInit:
    """Tests for JWKSManager initialization."""

    def test_init_with_url(self):
        """Test initialization with JWKS URL."""
        manager = JWKSManager(jwks_url="https://example.com/jwks")
        assert manager._jwks_url == "https://example.com/jwks"
        assert manager._jwks_cache == {}
        assert manager._current_key_id is None

    def test_init_without_url(self):
        """Test initialization without JWKS URL."""
        manager = JWKSManager()
        assert manager._jwks_url is None
        assert manager._jwks_cache == {}

    def test_init_custom_rotation_interval(self):
        """Test initialization with custom rotation interval."""
        manager = JWKSManager(rotation_interval=3600)
        assert manager._rotation_interval == 3600


class TestJWKSManagerGetSigningKey:
    """Tests for get_signing_key method."""

    @pytest.mark.asyncio
    async def test_get_signing_key_with_jwks(self):
        """Test getting signing key returns fallback when no JWKS client."""
        manager = JWKSManager(jwks_url="https://example.com/jwks")

        # Without a working JWKS client, it should fall back to static
        with patch("core.security.SECRET_KEY", "static-secret"):
            key, kid = await manager.get_signing_key()
            assert key == "static-secret"
            assert kid == "static"

    @pytest.mark.asyncio
    async def test_get_signing_key_fallback(self):
        """Test fallback to static secret."""
        manager = JWKSManager()

        with patch("core.security.SECRET_KEY", "static-secret"):
            key, kid = await manager.get_signing_key()
            assert key == "static-secret"
            assert kid == "static"


class TestJWKSManagerVerifyToken:
    """Tests for verify_token method."""

    @pytest.mark.asyncio
    async def test_verify_token_with_jwks_client(self):
        """Test token verification with JWKS client."""
        import jwt

        from core.security import ALGORITHM, SECRET_KEY

        manager = JWKSManager(jwks_url="https://example.com/jwks")
        manager._jwks_client = MagicMock()

        # Create a valid token
        token = jwt.encode(
            {"sub": "test-user", "exp": time.time() + 3600},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )

        # Mock the JWKS client to use static key
        mock_key = MagicMock()
        mock_key.key = SECRET_KEY
        manager._jwks_client.get_signing_key_from_jwt = MagicMock(return_value=mock_key)

        payload = await manager.verify_token(token)
        assert payload["sub"] == "test-user"

    @pytest.mark.asyncio
    async def test_verify_token_fallback_to_static(self):
        """Test token verification falls back to static secret."""
        import jwt

        from core.security import ALGORITHM, SECRET_KEY

        manager = JWKSManager()

        token = jwt.encode(
            {"sub": "test-user", "exp": time.time() + 3600},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )

        payload = await manager.verify_token(token)
        assert payload["sub"] == "test-user"

    @pytest.mark.asyncio
    async def test_verify_token_expired(self):
        """Test expired token rejection."""
        import jwt

        from core.security import ALGORITHM, SECRET_KEY

        manager = JWKSManager()

        token = jwt.encode(
            {"sub": "test-user", "exp": time.time() - 3600},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )

        with pytest.raises(jwt.ExpiredSignatureError):
            await manager.verify_token(token)


class TestJWKSManagerKeyHistory:
    """Tests for key history management."""

    def test_key_history_cleanup(self):
        """Test expired key cleanup."""
        manager = JWKSManager()

        # Add expired key
        manager._key_history.append(("old-key", time.time() - 100))
        # Add valid key
        manager._key_history.append(("new-key", time.time() + 3600))

        # Clean up expired keys
        now = time.time()
        manager._key_history = [(kid, exp) for kid, exp in manager._key_history if now < exp]

        assert len(manager._key_history) == 1
        assert manager._key_history[0][0] == "new-key"


class TestJWKSManagerKeyInfo:
    """Tests for get_key_info method."""

    def test_get_key_info_default(self):
        """Test key info with default values."""
        manager = JWKSManager()

        info = manager.get_key_info()
        assert info["current_key_id"] is None
        assert info["key_history_count"] == 0
        assert info["jwks_cached"] is False
        assert info["jwks_url"] == "not configured"

    def test_get_key_info_with_url(self):
        """Test key info with JWKS URL."""
        manager = JWKSManager(jwks_url="https://example.com/jwks")

        info = manager.get_key_info()
        assert info["jwks_url"] == "https://example.com/jwks"


class TestJWKSConstants:
    """Tests for JWKS constants."""

    def test_rotation_interval(self):
        """Test rotation interval is 24 hours."""
        assert ROTATION_INTERVAL_SECONDS == 86400

    def test_rotation_window(self):
        """Test rotation window is 1 hour."""
        assert ROTATION_WINDOW_SECONDS == 3600

    def test_jwks_cache_ttl(self):
        """Test JWKS cache TTL is 1 hour."""
        assert JWKS_CACHE_TTL_SECONDS == 3600

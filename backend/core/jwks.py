# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""JWKS-based API key rotation for SafeVixAI Backend.

Implements:
- Dynamic key fetching from JWKS endpoint
- Periodic key rotation (every 24 hours)
- Multiple valid secrets during rotation window
- Key version (kid) tracking in tokens

Phase 0.3: Prevents token theft from static secrets.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx
import jwt

logger = logging.getLogger(__name__)

# Rotation configuration
ROTATION_INTERVAL_SECONDS = 86400  # 24 hours
ROTATION_WINDOW_SECONDS = 3600     # 1-hour overlap for old keys
JWKS_CACHE_TTL_SECONDS = 3600      # Cache JWKS for 1 hour

# Supabase JWKS endpoint (if using Supabase Auth)
SUPABASE_JWKS_URL = "https://<project-ref>.supabase.co/auth/v1/jwks"


class JWKSManager:
    """Manages JSON Web Key Sets for API key rotation."""

    def __init__(
        self,
        jwks_url: str | None = None,
        rotation_interval: int = ROTATION_INTERVAL_SECONDS,
    ) -> None:
        self._jwks_url = jwks_url
        self._rotation_interval = rotation_interval
        self._jwks_cache: dict[str, Any] = {}
        self._jwks_cache_time = 0.0
        self._current_key_id: str | None = None
        self._key_history: list[tuple[str, float]] = []  # (kid, expiry_time)
        self._jwks_client: jwt.PyJWKClient | None = None
        self._rotation_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the JWKS manager and key rotation."""
        if self._jwks_url:
            self._jwks_client = jwt.PyJWKClient(self._jwks_url, cache_keys=True)
            await self._fetch_jwks()
            self._rotation_task = asyncio.create_task(self._rotation_loop())
            logger.info("JWKS manager started with URL: %s", self._jwks_url)
        else:
            logger.warning("No JWKS URL configured; using static secret rotation")

    async def stop(self) -> None:
        """Stop the JWKS manager."""
        if self._rotation_task:
            self._rotation_task.cancel()
            try:
                await self._rotation_task
            except asyncio.CancelledError:
                logger.info("JWKS rotation task cancelled (expected during shutdown)")
        logger.info("JWKS manager stopped")

    async def get_signing_key(self) -> tuple[str, str]:
        """Get the current signing key and its kid.
        
        Returns:
            Tuple of (key, kid) for signing tokens.
        """
        if self._jwks_client:
            jwks = await self._fetch_jwks()
            if jwks.get("keys"):
                key_data = jwks["keys"][0]
                kid = key_data.get("kid")
                key = jwt.PyJWK(key_data)
                return key.key, kid or "default"

        # Fallback to static secret
        from core.security import SECRET_KEY
        return SECRET_KEY, "static"

    async def verify_token(self, token: str) -> dict[str, Any]:
        """Verify a JWT token using current or historical keys.
        
        Tries current key first, then falls back to historical keys
        during the rotation window.
        """
        # Try current key first
        if self._jwks_client:
            try:
                signing_key = self._jwks_client.get_signing_key_from_jwt(token)
                return jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["RS256", "ES256"],
                    audience="authenticated",
                )
            except jwt.InvalidTokenError as e:
                logger.debug("Current key verification failed: %s", e)

        # Try historical keys during rotation window
        now = time.time()
        for kid, expiry_time in self._key_history:
            if now > expiry_time:
                continue  # Key expired

            try:
                key = self._jwks_cache.get(kid)
                if key:
                    return jwt.decode(
                        token,
                        key,
                        algorithms=["RS256", "ES256"],
                        audience="authenticated",
                    )
            except jwt.InvalidTokenError:
                continue

        # Fallback to static secret
        from core.security import ALGORITHM, SECRET_KEY
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.InvalidTokenError:
            raise

    async def rotate_keys(self) -> None:
        """Rotate to a new signing key."""
        if not self._jwks_url:
            logger.info("No JWKS URL; skipping rotation")
            return

        from core.distributed_lock import distributed_lock
        async with distributed_lock("jwks_rotation", ttl_seconds=10):
            old_key_id = self._current_key_id
            await self._fetch_jwks()

            if old_key_id and old_key_id != self._current_key_id:
                # Add old key to history with rotation window
                expiry = time.time() + ROTATION_WINDOW_SECONDS
                self._key_history.append((old_key_id, expiry))
                logger.info(
                    "Key rotated: %s -> %s (old key valid until %s)",
                    old_key_id,
                    self._current_key_id,
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(expiry)),
                )

            # Clean up expired keys
            now = time.time()
            self._key_history = [(kid, exp) for kid, exp in self._key_history if now < exp]

    async def _fetch_jwks(self) -> dict[str, Any]:
        """Fetch JWKS from the configured URL."""
        now = time.time()
        if now - self._jwks_cache_time < JWKS_CACHE_TTL_SECONDS and self._jwks_cache:
            return self._jwks_cache

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self._jwks_url, timeout=10.0)
                response.raise_for_status()
                jwks = response.json()

            self._jwks_cache = jwks
            self._jwks_cache_time = now

            # Update current key ID
            if jwks.get("keys"):
                self._current_key_id = jwks["keys"][0].get("kid", "default")

            return jwks
        except Exception as e:
            logger.error("Failed to fetch JWKS: %s", e)
            return self._jwks_cache or {}

    async def _rotation_loop(self) -> None:
        """Periodic key rotation loop."""
        while True:
            try:
                await asyncio.sleep(self._rotation_interval)
                await self.rotate_keys()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Key rotation failed: %s", e)

    def get_key_info(self) -> dict[str, Any]:
        """Get current key information for debugging."""
        return {
            "current_key_id": self._current_key_id,
            "key_history_count": len(self._key_history),
            "jwks_cached": bool(self._jwks_cache),
            "jwks_url": self._jwks_url or "not configured",
        }

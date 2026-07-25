# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Geocoding Utility — Nominatim (primary) + OpenCage (fallback).

Central geocoding for the chatbot service:
  - Nominatim: Free, 1 req/sec, requires User-Agent
  - OpenCage: Free tier 2500/day, needs OPENCAGE_API_KEY

Used by: crash detection, SOS message builder, context assembler.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential


def is_retriable_geocoding(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        # Do not retry on 4xx errors (like 403 Forbidden, 404 Not Found), EXCEPT 429 Too Many Requests
        return exc.response.status_code >= 500 or exc.response.status_code == 429
    return True

logger = logging.getLogger(__name__)
class GeocodingClient:
    """Reverse geocoding with Nominatim primary + OpenCage fallback."""

    NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
    OPENCAGE_URL = "https://api.opencagedata.com/geocode/v1/json"

    def __init__(
        self,
        *,
        opencage_key: str | None = None,
        timeout: float = 10.0,
        user_agent: str = "SafeVixAI/1.0 (team@safevixai.in)",
    ) -> None:
        self.opencage_key = opencage_key or os.getenv("OPENCAGE_API_KEY", "")
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": user_agent},
        )
        self._rate_limit_lock = asyncio.Lock()
        self._last_nominatim_request_at = 0.0

    async def reverse_geocode(self, *, lat: float, lon: float) -> dict | None:
        """Convert GPS coordinates to address. Tries Nominatim first, then OpenCage.

        Returns:
            {'road': '...', 'city': '...', 'state': '...', 'postcode': '...', 'display': '...'} or None
        """
        result = await self._nominatim_reverse(lat=lat, lon=lon)
        if result is not None:
            return result

        return await self._opencage_reverse(lat=lat, lon=lon)

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception(is_retriable_geocoding),
        reraise=True,
    )
    async def _nominatim_request(self, lat: float, lon: float) -> dict:
        async with self._rate_limit_lock:
            elapsed = time.monotonic() - self._last_nominatim_request_at
            if elapsed < 1.0:
                await asyncio.sleep(1.0 - elapsed)
            try:
                response = await self._client.get(
                    self.NOMINATIM_URL,
                    params={
                        "lat": lat,
                        "lon": lon,
                        "format": "json",
                        "addressdetails": 1,
                    },
                )
                response.raise_for_status()
                return response.json()
            finally:
                self._last_nominatim_request_at = time.monotonic()

    async def _nominatim_reverse(self, *, lat: float, lon: float) -> dict | None:
        """Nominatim reverse geocoding — free, 1 req/sec with robust rate limiting and retries."""
        try:
            data = await self._nominatim_request(lat=lat, lon=lon)
            addr = data.get("address", {})

            road = addr.get("road", "")
            city = addr.get("city") or addr.get("town") or addr.get("village", "")
            state = addr.get("state", "")
            postcode = addr.get("postcode", "")

            parts = [p for p in [road, city, state] if p]
            display = ", ".join(parts) or data.get("display_name", "Unknown")

            return {
                "road": road,
                "city": city,
                "state": state,
                "postcode": postcode,
                "display": display,
                "source": "nominatim",
            }
        except (httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError, Exception) as exc:
            logger.warning("Nominatim geocoding failed after retries: %s", exc)
        return None

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception(is_retriable_geocoding),
        reraise=True,
    )
    async def _opencage_request(self, lat: float, lon: float) -> dict:
        response = await self._client.get(
            self.OPENCAGE_URL,
            params={
                "q": f"{lat}+{lon}",
                "key": self.opencage_key,
                "no_annotations": 1,
                "language": "en",
            },
        )
        response.raise_for_status()
        return response.json()

    async def _opencage_reverse(self, *, lat: float, lon: float) -> dict | None:
        """OpenCage fallback — 2500/day free, better for small Indian towns."""
        if not self.opencage_key:
            return None
        try:
            data = await self._opencage_request(lat=lat, lon=lon)
            results = data.get("results", [])
            if not results:
                return None

            first = results[0]
            comp = first.get("components", {})

            road = comp.get("road", "")
            city = comp.get("city") or comp.get("town") or comp.get("village", "")
            state = comp.get("state", "")
            postcode = comp.get("postcode", "")
            display = first.get("formatted", "Unknown")

            return {
                "road": road,
                "city": city,
                "state": state,
                "postcode": postcode,
                "display": display,
                "source": "opencage",
            }
        except (httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError, Exception) as exc:
            logger.warning("OpenCage geocoding failed after retries: %s", exc)
        return None

    async def aclose(self) -> None:
        await self._client.aclose()


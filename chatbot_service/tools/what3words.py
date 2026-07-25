# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""What3Words API — convert GPS to 3-word address for SOS messages.

Requires W3W_API_KEY (free signup at developer.what3words.com).
Returns the iconic ///three.word.address format for exact location sharing.

This is a jury-demo moment: SOS says "Location: ///filled.count.soap"
"""

from __future__ import annotations

import json
import logging
import os

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential


def is_retriable_http(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500 or exc.response.status_code == 429
    return True


logger = logging.getLogger(__name__)

W3W_BASE_URL = "https://api.what3words.com/v3"


class What3WordsTool:
    """Convert GPS coordinates to a 3-word address and back."""

    def __init__(self, api_key: str | None = None, timeout: float = 10.0) -> None:
        self.api_key = api_key or os.getenv("W3W_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=timeout)

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3), retry=retry_if_exception(is_retriable_http), reraise=True)
    async def _request_gps_to_words(self, lat: float, lon: float) -> dict:
        response = await self._client.get(
            f"{W3W_BASE_URL}/convert-to-3wa",
            params={
                "coordinates": f"{lat},{lon}",
                "key": self.api_key,
            },
        )
        response.raise_for_status()
        return response.json()

    async def gps_to_words(self, *, lat: float, lon: float) -> dict | None:
        """Convert GPS coordinates to a 3-word address.

        Returns:
            {'words': 'filled.count.soap', 'map_url': 'https://w3w.co/filled.count.soap'}
            or None on failure.
        """
        if not self.api_key:
            return None

        try:
            data = await self._request_gps_to_words(lat=lat, lon=lon)
            words = data.get("words", "")
            if not words:
                return None

            return {
                "words": words,
                "map_url": f"https://w3w.co/{words}",
                "formatted": f"///{words}",
            }
        except (httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError, Exception) as exc:
            logger.warning("What3Words gps_to_words failed after retries: %s", exc)
        return None

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3), retry=retry_if_exception(is_retriable_http), reraise=True)
    async def _request_words_to_gps(self, words: str) -> dict:
        response = await self._client.get(
            f"{W3W_BASE_URL}/convert-to-coordinates",
            params={
                "words": words.replace("///", ""),
                "key": self.api_key,
            },
        )
        response.raise_for_status()
        return response.json()

    async def words_to_gps(self, words: str) -> dict | None:
        """Convert a 3-word address back to GPS coordinates.

        Returns:
            {'lat': 13.08, 'lon': 80.27} or None on failure.
        """
        if not self.api_key:
            return None

        try:
            data = await self._request_words_to_gps(words=words)
            coords = data.get("coordinates", {})
            return {
                "lat": coords.get("lat"),
                "lon": coords.get("lng"),
            }
        except (httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError, Exception) as exc:
            logger.warning("What3Words words_to_gps failed after retries: %s", exc)
        return None

    async def aclose(self) -> None:
        await self._client.aclose()


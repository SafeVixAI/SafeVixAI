# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Weather Tool — Open-Meteo (primary) + OpenWeatherMap (fallback).

Provides weather data for risk assessment and chatbot context.
Open-Meteo is free with no API key. OWM is the fallback if Open-Meteo fails.
"""

from __future__ import annotations

import json
import logging

import httpx

from config import Settings

logger = logging.getLogger(__name__)
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential  # noqa: E402

from tools.open_meteo import OpenMeteoClient  # noqa: E402


def is_retriable_http(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500 or exc.response.status_code == 429
    return True


class WeatherTool:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._open_meteo = OpenMeteoClient(settings)
        self._owm_client = httpx.AsyncClient(
            timeout=settings.http_timeout_seconds,
            headers={'User-Agent': settings.http_user_agent},
        )

    async def lookup(self, *, lat: float, lon: float) -> dict | None:
        """Try Open-Meteo first (free, no key), fall back to OpenWeatherMap."""

        # Primary: Open-Meteo — free, unlimited, no key
        result = await self._open_meteo.lookup(lat=lat, lon=lon)
        if result is not None:
            return result

        # Fallback: OpenWeatherMap — needs API key
        return await self._owm_lookup(lat=lat, lon=lon)

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3), retry=retry_if_exception(is_retriable_http), reraise=True)
    async def _owm_request(self, lat: float, lon: float) -> dict:
        response = await self._owm_client.get(
            f'{self.settings.openweather_base_url}/weather',
            params={
                'lat': lat,
                'lon': lon,
                'appid': self.settings.openweather_api_key,
                'units': self.settings.openweather_units,
            },
        )
        response.raise_for_status()
        return response.json()

    async def _owm_lookup(self, *, lat: float, lon: float) -> dict | None:
        """OpenWeatherMap fallback — requires OPENWEATHER_API_KEY with robust retries."""
        if not self.settings.openweather_api_key:
            return None
        try:
            payload = await self._owm_request(lat=lat, lon=lon)
            weather = payload.get('weather') or [{}]
            main = payload.get('main') or {}
            return {
                'summary': weather[0].get('description') or 'Weather unavailable',
                'temperature': main.get('temp'),
                'source': 'openweathermap',
            }
        except (httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError, Exception) as exc:
            logger.warning("OpenWeatherMap failed after retries: %s", exc)
        return None

    async def aclose(self) -> None:
        await self._open_meteo.aclose()
        await self._owm_client.aclose()


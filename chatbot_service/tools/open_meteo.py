# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Open-Meteo Weather API — free, no key, unlimited.

Used as the PRIMARY weather source. OpenWeatherMap becomes fallback.
Endpoint: https://api.open-meteo.com/v1/forecast
"""

from __future__ import annotations

import asyncio
import json
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

def is_retriable_http(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500 or exc.response.status_code == 429
    return True


from config import Settings

logger = logging.getLogger(__name__)

# Weather code → description mapping (WMO codes)
_WMO_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

# Risk multiplier based on weather code
_RISK_MULTIPLIERS: dict[int, float] = {
    0: 1.0, 1: 1.0, 2: 1.0, 3: 1.1,
    45: 1.8, 48: 2.0,   # Fog — high risk
    51: 1.3, 53: 1.4, 55: 1.5,
    56: 1.8, 57: 2.0,   # Freezing — very high
    61: 1.4, 63: 1.6, 65: 1.8,
    66: 2.0, 67: 2.2,
    71: 1.5, 73: 1.7, 75: 2.0,
    77: 1.6,
    80: 1.4, 81: 1.6, 82: 2.0,
    85: 1.6, 86: 2.0,
    95: 2.2, 96: 2.5, 99: 3.0,
}


class OpenMeteoClient:
    """Free weather data from Open-Meteo — no key required."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, settings: Settings) -> None:
        self._client = httpx.AsyncClient(
            timeout=settings.http_timeout_seconds,
            headers={"User-Agent": settings.http_user_agent},
        )

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3), retry=retry_if_exception(is_retriable_http), reraise=True)
    async def _request(self, lat: float, lon: float) -> dict:
        response = await self._client.get(
            self.BASE_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true",
                "hourly": "precipitation_probability,visibility",
                "forecast_days": 1,
                "timezone": "auto",
            },
        )
        response.raise_for_status()
        return response.json()

    async def lookup(self, *, lat: float, lon: float) -> dict | None:
        """Fetch current weather + hourly precipitation/visibility for risk model."""
        try:
            data = await self._request(lat=lat, lon=lon)
            current = data.get("current_weather", {})
            weather_code = current.get("weathercode", 0)
            temperature = current.get("temperature")
            wind_speed = current.get("windspeed")

            # Get current hour's precipitation probability and visibility
            hourly = data.get("hourly", {})
            precip_probs = hourly.get("precipitation_probability", [])
            visibilities = hourly.get("visibility", [])

            # Use first value (current hour)
            precip_prob = precip_probs[0] if precip_probs else None
            visibility = visibilities[0] if visibilities else None

            summary = _WMO_CODES.get(weather_code, "Unknown")
            base_risk = _RISK_MULTIPLIERS.get(weather_code, 1.0)

            # Increase risk for low visibility
            if visibility is not None and visibility < 1000:
                risk = max(base_risk, 2.0)
            elif visibility is not None and visibility < 5000:
                risk = max(base_risk, 1.5)
            else:
                risk = base_risk

            return {
                "summary": summary,
                "temperature": temperature,
                "wind_speed_kmh": wind_speed,
                "precipitation_probability": precip_prob,
                "visibility_meters": visibility,
                "weather_code": weather_code,
                "risk_multiplier": risk,
                "source": "open-meteo",
            }
        except (httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError, Exception) as exc:
            logger.warning("Open-Meteo failed after retries: %s", exc)
        return None

    async def aclose(self) -> None:
        await self._client.aclose()


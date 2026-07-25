# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Fetches nearby safe public spaces using Overpass API with graceful fallback."""
from __future__ import annotations

import logging

import httpx

from core.circuit_breaker import CircuitBreakerOpenError, CircuitBreakerRegistry
from services.exceptions import ServiceValidationError

logger = logging.getLogger(__name__)

# Shared long-lived client — lazily created on first request to avoid event loop issues at import
_CLIENT: httpx.AsyncClient | None = None


async def close_safe_spaces_client() -> None:
    """Cleanup the global HTTP client on application shutdown."""
    global _CLIENT
    if _CLIENT is not None and not _CLIENT.is_closed:
        await _CLIENT.aclose()
        _CLIENT = None


async def _do_safe_spaces_request(endpoint: str, query: str) -> httpx.Response:
    return await _CLIENT.post(endpoint, data={'data': query})


async def get_safe_spaces(lat: float, lon: float, radius_m: int = 1000) -> dict:
    """
    Returns nearby safe spaces: restaurants, cafes, pharmacies, hospitals, police.
    Uses Overpass API — free, no key, real-time OSM data.
    Falls back to an empty list with a warning if all endpoints are rate-limited.
    """
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        msg = f"Invalid coordinates: lat={lat}, lon={lon}"
        raise ServiceValidationError(msg)
    if radius_m is not None and (radius_m < 100 or radius_m > 100000):
        msg = f"Invalid radius: {radius_m}"
        raise ServiceValidationError(msg)
    global _CLIENT
    if _CLIENT is None or _CLIENT.is_closed:
        _CLIENT = httpx.AsyncClient(timeout=20.0)

    query = f"""
[out:json][timeout:15];
(
  node[amenity~"restaurant|cafe|pharmacy|hospital|police|fire_station"][name]
      (around:{radius_m},{lat},{lon});
  node[shop~"supermarket|convenience|medical|mall"][name]
      (around:{radius_m},{lat},{lon});
);
out body;
""".strip()

    endpoints = [
        'https://overpass-api.de/api/interpreter',
        'https://overpass.kumi.systems/api/interpreter',
        'https://overpass.private.coffee/api/interpreter',
    ]

    cb = CircuitBreakerRegistry.get("safe_spaces", failure_threshold=5, recovery_timeout=60.0)
    for endpoint in endpoints:
        try:
            r = await cb.call(_do_safe_spaces_request, endpoint, query)

            # Rate limit — try next mirror
            if r.status_code in (406, 429, 503):
                continue

            # Any other HTTP error
            if r.status_code >= 400:
                continue

            elements = r.json().get('elements', [])
            places = [
                {
                    'name': e['tags'].get('name', 'Unknown'),
                    'type': e['tags'].get('amenity', e['tags'].get('shop', 'place')),
                    'lat': e['lat'],
                    'lon': e['lon'],
                    'phone': e['tags'].get('phone') or e['tags'].get('contact:phone'),
                    'open_hours': e['tags'].get('opening_hours'),
                }
                for e in elements
                if 'lat' in e and 'lon' in e
            ]
            return {
                'places': places,
                'count': len(places),
                'radius_meters': radius_m,
                'source': 'openstreetmap',
            }

        except CircuitBreakerOpenError:
            logger.warning("Safe spaces circuit breaker OPEN — skipping remaining endpoints", extra={"service": "safe_spaces"})
            break
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            logger.warning('Overpass API request failed: %s', exc, extra={"service": "safe_spaces"})
            continue

    # All endpoints failed — return graceful empty response (never 500)
    return {
        'places': [],
        'count': 0,
        'radius_meters': radius_m,
        'source': 'openstreetmap',
        'warning': (
            'Safe spaces data temporarily unavailable '
            '(Overpass API rate limit). Try again shortly.'
        ),
    }

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Safe routing — avoids isolated road stretches at night using ORS or OSRM fallback."""
from __future__ import annotations

import logging
import os
from datetime import datetime

import httpx

from core.circuit_breaker import CircuitBreakerOpenError, CircuitBreakerRegistry
from services.exceptions import ExternalServiceError, ServiceValidationError

logger = logging.getLogger("safevixai.backend.safe_routing")


class Clock:
    """Abstraction over datetime for testability."""
    def now(self) -> datetime:
        return datetime.now()


_clock: Clock = Clock()


def set_clock(clock: Clock) -> None:
    """Override the clock for testing. Pass a custom Clock to control time."""
    global _clock
    _clock = clock


def _validate_coords(origin: tuple[float, float], dest: tuple[float, float]) -> None:
    """Validate coordinate ranges before making external API calls."""
    for label, (lat, lon) in [("origin", origin), ("dest", dest)]:
        if not (-90 <= lat <= 90):
            msg = f"{label} latitude {lat} out of range (-90..90)"
            raise ServiceValidationError(msg)
        if not (-180 <= lon <= 180):
            msg = f"{label} longitude {lon} out of range (-180..180)"
            raise ServiceValidationError(msg)


def is_nighttime() -> bool:
    """Returns True between 8pm and 6am."""
    hour = _clock.now().hour
    return hour >= 20 or hour <= 6


async def get_safe_route(
    origin: tuple[float, float],
    dest: tuple[float, float],
    prefer_safety: bool = False,
) -> dict:
    """
    Safe routing for night travel.
    - Uses ORS when OPENROUTESERVICE_API_KEY is present (avoids tracks/fords).
    - Falls back gracefully to free OSRM when no ORS key is configured.
    """
    _validate_coords(origin, dest)
    ors_key = os.getenv('OPENROUTESERVICE_API_KEY', '').strip()
    safety_mode = prefer_safety or is_nighttime()

    if ors_key:
        cb = CircuitBreakerRegistry.get("ors_safe", failure_threshold=3, recovery_timeout=30.0)
        try:
            data = await cb.call(_do_ors_safe_request, ors_key, origin, dest, safety_mode)
        except CircuitBreakerOpenError:
            logger.warning("ORS safe routing circuit breaker OPEN, falling back to OSRM", extra={"service": "safe_routing"})
            return await _osrm_fallback(origin, dest, safety_mode)
        except (httpx.TimeoutException, httpx.HTTPError) as exc:
            logger.warning("ORS safe routing failed: %s, falling back to OSRM", exc, extra={"service": "safe_routing"})
            return await _osrm_fallback(origin, dest, safety_mode)

        try:
            route = data['routes'][0]
            return {
                'provider': 'ors_safe',
                'safety_mode': safety_mode,
                'note': (
                    'Route optimized for safety — avoids isolated tracks and roads'
                    if safety_mode else 'Standard ORS route'
                ),
                'distance_meters': route['summary']['distance'],
                'duration_seconds': route['summary']['duration'],
                'geometry': route['geometry'],
            }
        except (KeyError, IndexError, TypeError) as exc:
            logger.error("ORS response parse failed: %s", exc, extra={"service": "safe_routing"})
            msg = "Invalid response from ORS routing service"
            raise ExternalServiceError(msg) from exc

    return await _osrm_fallback(origin, dest, safety_mode)


async def _do_ors_safe_request(ors_key: str, origin: tuple[float, float], dest: tuple[float, float], safety_mode: bool) -> dict:
    url = 'https://api.openrouteservice.org/v2/directions/driving-car/json'
    body: dict = {
        'coordinates': [[origin[1], origin[0]], [dest[1], dest[0]]],
        'preference': 'recommended',
        'extra_info': ['waycategory', 'waytype'],
    }
    if safety_mode:
        body['options'] = {'avoid_features': ['tracks', 'fords']}
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(
            url,
            json=body,
            headers={'Authorization': ors_key, 'Content-Type': 'application/json'},
        )
        r.raise_for_status()
        return r.json()


async def _do_osrm_safe_request(origin: tuple[float, float], dest: tuple[float, float]) -> dict:
    osrm_url = (
        f'https://router.project-osrm.org/route/v1/driving/'
        f'{origin[1]},{origin[0]};{dest[1]},{dest[0]}'
    )
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            osrm_url,
            params={'overview': 'full', 'geometries': 'geojson', 'steps': 'false'},
        )
        r.raise_for_status()
        return r.json()


async def _osrm_fallback(
    origin: tuple[float, float],
    dest: tuple[float, float],
    safety_mode: bool,
) -> dict:
    """Free OSRM fallback when no ORS key is configured or ORS fails."""
    cb = CircuitBreakerRegistry.get("osrm_safe", failure_threshold=3, recovery_timeout=30.0)
    try:
        data = await cb.call(_do_osrm_safe_request, origin, dest)
    except CircuitBreakerOpenError:
        logger.error("OSRM fallback circuit breaker OPEN for coords %s, %s", origin, dest, extra={"service": "safe_routing"})
        msg = "Routing service unavailable — try again later"
        raise ExternalServiceError(msg)
    except (httpx.TimeoutException, httpx.HTTPError) as exc:
        logger.error("OSRM fallback HTTP error: %s", exc, extra={"service": "safe_routing"})
        msg = "Routing service unavailable — try again later"
        raise ExternalServiceError(msg) from exc

    routes = data.get('routes') or []
    if not routes:
        logger.error("OSRM returned empty routes for coords %s → %s", origin, dest, extra={"service": "safe_routing"})
        msg = "No route found between the given locations"
        raise ExternalServiceError(msg)

    route = routes[0]
    return {
        'provider': 'osrm_fallback',
        'safety_mode': safety_mode,
        'note': (
            'Safety routing unavailable without ORS key — using standard OSRM route.'
            if safety_mode else 'Standard OSRM route (no ORS key configured).'
        ),
        'distance_meters': route.get('distance', 0),
        'duration_seconds': route.get('duration', 0),
        'geometry': route.get('geometry', {}),
    }

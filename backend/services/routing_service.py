# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import httpx

from core.circuit_breaker import CircuitBreakerOpenError, CircuitBreakerRegistry
from core.config import Settings
from core.redis_client import CacheHelper
from models.schemas import (
    RouteBounds,
    RouteInstruction,
    RouteOption,
    RoutePoint,
    RoutePreviewResponse,
    RouteProfile,
)
from services.exceptions import ExternalServiceError, ServiceValidationError

# alert_service.py at project root
for parent in Path(__file__).resolve().parents:
    if (parent / 'alert_service.py').exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break
from core.alert import get_alert_service

logger = logging.getLogger("safevixai.backend.routing")


class RoutingService:
    def __init__(self, settings: Settings, cache: CacheHelper) -> None:
        self.settings = settings
        self.cache = cache
        self._client = httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            headers={
                'Accept': 'application/json',
                'User-Agent': settings.http_user_agent,
            },
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def preview_route(
        self,
        *,
        origin_lat: float,
        origin_lon: float,
        destination_lat: float,
        destination_lon: float,
        profile: RouteProfile = 'driving-car',
        alternatives: int = 2,
    ) -> RoutePreviewResponse:
        if self._same_point(origin_lat, origin_lon, destination_lat, destination_lon):
            raise ServiceValidationError('Origin and destination are too close to calculate a route.')

        requested_alternatives = max(0, min(int(alternatives), 2))
        cache_key = (
            'route:preview:'
            f'{profile}:{requested_alternatives}:'
            f'{origin_lat:.5f}:{origin_lon:.5f}:{destination_lat:.5f}:{destination_lon:.5f}'
        )
        cached = await self.cache.get_json(cache_key)
        if cached:
            return RoutePreviewResponse.model_validate(cached)

        warnings: list[str] = []
        is_ors = bool(self.settings.openrouteservice_api_key)

        if is_ors:
            # ORS — needs API key, supports alternatives
            url = (
                f'{self.settings.openrouteservice_base_url}'
                f'/v2/directions/{profile}/json'
            )
            body: dict = {
                'coordinates': [
                    [origin_lon, origin_lat],
                    [destination_lon, destination_lat],
                ],
                'preference': 'recommended',
                'instructions': True,
            }
            if requested_alternatives > 0:
                body['alternative_routes'] = {
                    'target_count': requested_alternatives,
                    'weight_factor': 1.4,
                }
            try:
                cb = CircuitBreakerRegistry.get("ors_routing", failure_threshold=3, recovery_timeout=30.0)
                response = await cb.call(self._do_ors_request, url, body)
            except CircuitBreakerOpenError:
                get_alert_service().alert_external_api_failed(
                    service_name="OpenRouteService (Routing)",
                    endpoint=url,
                    status_code=0,
                    error_msg="Circuit breaker OPEN — too many ORS failures",
                )
                raise ExternalServiceError('Unable to reach ORS routing provider.')
            except ExternalServiceError:
                raise
        else:
            # OSRM — free, no API key needed
            warnings.append('Using public OSRM routing (no ORS key configured).')
            url = (
                f'https://router.project-osrm.org/route/v1/driving/'
                f'{origin_lon},{origin_lat};{destination_lon},{destination_lat}'
            )
            params: dict = {
                'overview': 'full',
                'geometries': 'geojson',
                'steps': 'true',
            }
            if requested_alternatives > 0:
                params['alternatives'] = str(requested_alternatives)
            try:
                cb = CircuitBreakerRegistry.get("osrm_routing", failure_threshold=3, recovery_timeout=30.0)
                response = await cb.call(self._do_osrm_request, url, params)
            except CircuitBreakerOpenError:
                get_alert_service().alert_external_api_failed(
                    service_name="OSRM (Routing)",
                    endpoint=url,
                    status_code=0,
                    error_msg="Circuit breaker OPEN — too many OSRM failures",
                )
                raise ExternalServiceError('Unable to reach OSRM routing provider.')

        data = response.json()
        if response.status_code >= 400:
            raise ExternalServiceError(self._message_from_response(response))

        # ORS wraps routes under 'routes', OSRM under 'routes' too
        routes_data = data.get('routes') or []
        if not routes_data:
            raise ExternalServiceError('Routing provider returned no route.')

        if is_ors:
            routes = [self._normalize_ors_route(r, index=idx) for idx, r in enumerate(routes_data, start=1)]
        else:
            routes = [self._normalize_osrm_route(r, index=idx) for idx, r in enumerate(routes_data, start=1)]

        selected_route = routes[0]
        route = RoutePreviewResponse(
            provider='ors' if is_ors else 'osrm',
            profile=profile,
            distance_meters=selected_route.distance_meters,
            duration_seconds=selected_route.duration_seconds,
            path=selected_route.path,
            bounds=selected_route.bounds,
            origin=RoutePoint(lat=origin_lat, lon=origin_lon, label='Current location'),
            destination=RoutePoint(lat=destination_lat, lon=destination_lon, label='Destination'),
            steps=selected_route.steps,
            routes=routes,
            selected_route_id=selected_route.route_id,
            warnings=warnings or [],
        )

        await self.cache.set_json(
            cache_key,
            route.model_dump(mode='json'),
            self.settings.route_cache_ttl_seconds,
        )
        return route

    async def _do_ors_request(self, url: str, body: dict) -> httpx.Response:
        try:
            response = await self._client.post(
                url,
                json=body,
                headers={'Authorization': self.settings.openrouteservice_api_key},
            )
            return response
        except httpx.HTTPError as exc:
            get_alert_service().alert_external_api_failed(
                service_name="OpenRouteService (Routing)",
                endpoint=url,
                status_code=0,
                error_msg=str(exc),
            )
            raise ExternalServiceError('Unable to reach ORS routing provider.') from exc

    async def _do_osrm_request(self, url: str, params: dict) -> httpx.Response:
        try:
            response = await self._client.get(url, params=params)
            return response
        except httpx.HTTPError as exc:
            get_alert_service().alert_external_api_failed(
                service_name="OSRM (Routing)",
                endpoint=url,
                status_code=0,
                error_msg=str(exc),
            )
            raise ExternalServiceError('Unable to reach OSRM routing provider.') from exc

    @staticmethod
    def _same_point(
        origin_lat: float,
        origin_lon: float,
        destination_lat: float,
        destination_lon: float,
    ) -> bool:
        return abs(origin_lat - destination_lat) < 1e-5 and abs(origin_lon - destination_lon) < 1e-5

    @staticmethod
    def _message_from_response(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            payload = None

        if isinstance(payload, dict):
            message = payload.get('error') or payload.get('message')
            if isinstance(message, dict):
                message = message.get('message')
            if isinstance(message, str) and message.strip():
                return message.strip()
        if response.status_code == 429:
            return 'Routing provider rate limit reached. Please try again in a moment.'
        return 'Routing provider could not generate a route right now.'

    @staticmethod
    def _decode_polyline(encoded: str, precision: int = 5) -> list[tuple[float, float]]:
        """Decode a Google-encoded polyline string into (lat, lon) tuples."""
        factor = 10 ** precision
        result: list[tuple[float, float]] = []
        index = lat = lng = 0
        while index < len(encoded):
            for is_lng in (False, True):
                shift = result_val = 0
                while True:
                    b = ord(encoded[index]) - 63
                    index += 1
                    result_val |= (b & 0x1F) << shift
                    shift += 5
                    if b < 0x20:
                        break
                delta = ~(result_val >> 1) if result_val & 1 else result_val >> 1
                if is_lng:
                    lng += delta
                else:
                    lat += delta
            result.append((lat / factor, lng / factor))
        return result

    def _normalize_ors_route(self, route_data: dict[str, Any], *, index: int) -> RouteOption:
        """Normalize an ORS /v2/directions/json route object."""
        geometry = route_data.get('geometry', '')
        path: list[RoutePoint] = []

        if isinstance(geometry, str) and geometry:
            for lat, lon in self._decode_polyline(geometry):
                try:
                    path.append(RoutePoint(lat=lat, lon=lon))
                except (TypeError, ValueError):
                    continue
        elif isinstance(geometry, dict):
            for coord in geometry.get('coordinates') or []:
                try:
                    path.append(RoutePoint(lat=float(coord[1]), lon=float(coord[0])))
                except (TypeError, IndexError, ValueError):
                    continue

        if len(path) < 2:
            raise ExternalServiceError('ORS returned invalid route geometry.')

        summary = route_data.get('summary') or {}
        steps: list[RouteInstruction] = []
        for seg in route_data.get('segments') or []:
            for step_index, step in enumerate(seg.get('steps') or [], start=len(steps) + 1):
                steps.append(
                    RouteInstruction(
                        index=step_index,
                        instruction=str(step.get('instruction') or 'Continue'),
                        distance_meters=float(step.get('distance') or 0.0),
                        duration_seconds=float(step.get('duration') or 0.0),
                        street_name=step.get('name') or None,
                    )
                )

        label = 'Primary route' if index == 1 else f'Alternative {index - 1}'
        return RouteOption(
            route_id=f'route-{index}',
            label=label,
            distance_meters=float(summary.get('distance') or 0.0),
            duration_seconds=float(summary.get('duration') or 0.0),
            path=path,
            bounds=self._build_bounds(path),
            steps=steps,
        )

    def _normalize_osrm_route(self, route_data: dict[str, Any], *, index: int) -> RouteOption:
        geometry = route_data.get('geometry')
        path: list[RoutePoint] = []

        # Primary: GeoJSON geometry dict with [lon, lat] coordinate pairs
        if isinstance(geometry, dict):
            for coord in geometry.get('coordinates') or []:
                try:
                    path.append(RoutePoint(lat=float(coord[1]), lon=float(coord[0])))
                except (TypeError, IndexError, ValueError):
                    continue

        # Fallback: encoded polyline string — extract points from step maneuver locations
        if len(path) < 2:
            for leg in route_data.get('legs') or []:
                for step in leg.get('steps') or []:
                    loc = (step.get('maneuver') or {}).get('location')
                    if loc and len(loc) >= 2:
                        try:
                            path.append(RoutePoint(lat=float(loc[1]), lon=float(loc[0])))
                        except (TypeError, ValueError):
                            continue

        if len(path) < 2:
            raise ExternalServiceError('Routing provider returned invalid path coordinates.')

        steps: list[RouteInstruction] = []
        legs = route_data.get('legs') or []
        for leg in legs:
            for step_index, step in enumerate(leg.get('steps') or [], start=len(steps) + 1):
                maneuver = step.get('maneuver') or {}
                instruction = maneuver.get('type')
                if maneuver.get('modifier'):
                    instruction += f" {maneuver.get('modifier')}"
                if step.get('name'):
                    instruction += f" on {step.get('name')}"

                steps.append(
                    RouteInstruction(
                        index=step_index,
                        instruction=str(instruction or 'Continue'),
                        distance_meters=float(step.get('distance') or 0.0),
                        duration_seconds=float(step.get('duration') or 0.0),
                        street_name=step.get('name') or None,
                    )
                )

        label = 'Primary route' if index == 1 else f'Alternative {index - 1}'
        return RouteOption(
            route_id=f'route-{index}',
            label=label,
            distance_meters=float(route_data.get('distance') or 0.0),
            duration_seconds=float(route_data.get('duration') or 0.0),
            path=path,
            bounds=self._build_bounds(path),
            steps=steps,
        )

    @staticmethod
    def _build_bounds(path: list[RoutePoint]) -> RouteBounds:
        lats = [point.lat for point in path]
        lons = [point.lon for point in path]
        return RouteBounds(
            south=min(lats),
            west=min(lons),
            north=max(lats),
            east=max(lons),
        )

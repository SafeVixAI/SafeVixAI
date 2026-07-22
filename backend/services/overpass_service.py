# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
import logging
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx

from core.circuit_breaker import CircuitBreakerOpenError, CircuitBreakerRegistry
from core.config import Settings
from models.schemas import EmergencyServiceItem
from services.exceptions import ExternalServiceError

# alert_service.py at project root
for parent in Path(__file__).resolve().parents:
    if (parent / 'alert_service.py').exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break
from core.alert import get_alert_service

logger = logging.getLogger("safevixai.backend.overpass")


@dataclass(slots=True)
class RoadContext:
    road_type_code: str
    road_type: str
    road_name: str | None
    road_number: str | None
    tags: dict[str, str]
    distance_meters: float


class OverpassService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            headers={'User-Agent': settings.http_user_agent},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def search_services(
        self,
        *,
        lat: float,
        lon: float,
        radius: int,
        categories: list[str],
        limit: int,
    ) -> list[EmergencyServiceItem]:
        query = self._build_service_query(lat=lat, lon=lon, radius=radius)
        payload = await self._execute_query(query)
        items: list[EmergencyServiceItem] = []
        for element in payload.get('elements', []):
            tags = element.get('tags', {})
            category = self._classify_service(tags)
            if not category or category not in categories:
                continue

            point_lat, point_lon = self._extract_point(element)
            if point_lat is None or point_lon is None:
                continue

            distance = self._haversine_distance(lat, lon, point_lat, point_lon)
            items.append(
                EmergencyServiceItem(
                    id=str(element.get('id', f'osm-{category}-{point_lat}-{point_lon}')),
                    name=tags.get('name') or f'{category.title()} service',
                    category=category,
                    sub_category=self._sub_category(tags),
                    phone=tags.get('phone') or tags.get('contact:phone'),
                    phone_emergency=tags.get('emergency:phone'),
                    lat=point_lat,
                    lon=point_lon,
                    distance_meters=distance,
                    has_trauma=self._has_trauma(tags),
                    has_icu=self._has_icu(tags),
                    is_24hr=self._is_24hr(tags),
                    address=self._compose_address(tags),
                    source='overpass',
                )
            )

        items.sort(key=lambda item: (0 if item.has_trauma else 1, 0 if item.is_24hr else 1, item.distance_meters))
        return items[:limit]

    async def get_road_context(self, *, lat: float, lon: float) -> RoadContext | None:
        query = self._build_road_query(lat=lat, lon=lon)
        payload = await self._execute_query(query)

        best: RoadContext | None = None
        for element in payload.get('elements', []):
            tags = element.get('tags', {})
            highway = tags.get('highway')
            if not highway:
                continue

            point_lat, point_lon = self._extract_point(element)
            if point_lat is None or point_lon is None:
                continue

            road_type_code, road_type = self.classify_road_type(tags)
            distance = self._haversine_distance(lat, lon, point_lat, point_lon)
            candidate = RoadContext(
                road_type_code=road_type_code,
                road_type=road_type,
                road_name=tags.get('name'),
                road_number=tags.get('ref'),
                tags=tags,
                distance_meters=distance,
            )
            if best is None or candidate.distance_meters < best.distance_meters:
                best = candidate
        return best

    @staticmethod
    def classify_road_type(tags: dict[str, str]) -> tuple[str, str]:
        highway = (tags.get('highway') or '').lower()
        ref = (tags.get('ref') or '').upper()
        if ref.startswith('NH') or highway == 'trunk':
            return 'NH', 'National Highway'
        if ref.startswith('SH') or highway == 'primary':
            return 'SH', 'State Highway'
        if ref.startswith('MDR') or highway == 'secondary':
            return 'MDR', 'Major District Road'
        if highway in {'unclassified', 'track'}:
            return 'VILLAGE', 'Village Road'
        return 'URBAN', 'Urban Road'

    async def _execute_query(self, query: str) -> dict:
        cb = CircuitBreakerRegistry.get("overpass", failure_threshold=3, recovery_timeout=60.0)
        try:
            return await cb.call(self._do_execute_query, query)
        except CircuitBreakerOpenError:
            logger.warning("Overpass circuit breaker OPEN — skipping query")
            get_alert_service().alert_external_api_failed(
                service_name="Overpass API",
                endpoint="_execute_query",
                status_code=0,
                error_msg="Circuit breaker OPEN — too many failures",
            )
            raise ExternalServiceError("Overpass API temporarily unavailable")
        except ExternalServiceError:
            raise

    async def _do_execute_query(self, query: str) -> dict:
        last_error: Exception | None = None
        for index, url in enumerate(self.settings.overpass_urls):
            # P1-06: Exponential backoff for Overpass API to handle 429s (audit H26)
            for attempt in range(self.settings.upstream_retry_attempts + 1):
                try:
                    response = await self._client.post(url, data={'data': query})
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPStatusError as exc:
                    last_error = exc
                    if exc.response.status_code not in (429, 500, 502, 503, 504):
                        break  # Non-retryable error, try next mirror if any

                    logger.warning("Overpass mirror %s failed (attempt %d): %s", url, attempt + 1, exc, extra={"service": "overpass"})
                    if attempt < self.settings.upstream_retry_attempts:
                        backoff = self.settings.upstream_retry_backoff_seconds * (2 ** attempt)
                        await asyncio.sleep(backoff)
                except httpx.RequestError as exc:
                    last_error = exc
                    logger.warning("Overpass mirror %s connection error: %s", url, exc, extra={"service": "overpass"})
                    break  # Try next mirror

            if index < len(self.settings.overpass_urls) - 1:
                await asyncio.sleep(self.settings.upstream_retry_backoff_seconds)
        # All mirrors exhausted — alert the team
        get_alert_service().alert_external_api_failed(
            service_name="Overpass API (Emergency Locator)",
            endpoint=f"POST {self.settings.overpass_urls}",
            status_code=0,
            error_msg=f"All {len(self.settings.overpass_urls)} mirrors failed: {last_error}",
        )
        raise ExternalServiceError('Overpass API unavailable') from last_error

    def _build_service_query(self, *, lat: float, lon: float, radius: int) -> str:
        return f"""
[out:json][timeout:25];
(
  node(around:{radius},{lat},{lon})[amenity~"hospital|clinic|police|fire_station|pharmacy"];
  way(around:{radius},{lat},{lon})[amenity~"hospital|clinic|police|fire_station|pharmacy"];
  relation(around:{radius},{lat},{lon})[amenity~"hospital|clinic|police|fire_station|pharmacy"];
  node(around:{radius},{lat},{lon})[emergency="ambulance_station"];
  way(around:{radius},{lat},{lon})[emergency="ambulance_station"];
  node(around:{radius},{lat},{lon})[shop~"car_repair|tyres"];
  way(around:{radius},{lat},{lon})[shop~"car_repair|tyres"];
  node(around:{radius},{lat},{lon})[craft="mechanic"];
  way(around:{radius},{lat},{lon})[craft="mechanic"];
);
out center tags;
""".strip()

    def _build_road_query(self, *, lat: float, lon: float) -> str:
        return f"""
[out:json][timeout:20];
(
  way(around:120,{lat},{lon})[highway];
);
out center tags;
""".strip()

    @staticmethod
    def _extract_point(element: dict) -> tuple[float | None, float | None]:
        if 'lat' in element and 'lon' in element:
            return float(element['lat']), float(element['lon'])
        center = element.get('center') or {}
        if 'lat' in center and 'lon' in center:
            return float(center['lat']), float(center['lon'])
        return None, None

    @staticmethod
    def _compose_address(tags: dict[str, str]) -> str | None:
        parts = [
            tags.get('addr:housenumber'),
            tags.get('addr:street'),
            tags.get('addr:suburb'),
            tags.get('addr:city') or tags.get('addr:town') or tags.get('addr:village'),
            tags.get('addr:state'),
        ]
        cleaned = [part for part in parts if part]
        return ', '.join(cleaned) if cleaned else None

    @staticmethod
    def _classify_service(tags: dict[str, str]) -> str | None:
        amenity = (tags.get('amenity') or '').lower()
        emergency = (tags.get('emergency') or '').lower()
        shop = (tags.get('shop') or '').lower()
        craft = (tags.get('craft') or '').lower()
        if amenity in {'hospital', 'clinic'}:
            return 'hospital'
        if amenity == 'police':
            return 'police'
        if amenity == 'fire_station':
            return 'fire'
        if amenity == 'pharmacy':
            return 'pharmacy'
        if emergency == 'ambulance_station':
            return 'ambulance'
        if shop in {'car_repair', 'tyres'} or craft == 'mechanic':
            return 'towing'
        return None

    @staticmethod
    def _sub_category(tags: dict[str, str]) -> str | None:
        if OverpassService._has_trauma(tags):
            return 'trauma_centre'
        if OverpassService._has_icu(tags):
            return 'icu'
        healthcare = tags.get('healthcare')
        return healthcare.lower() if healthcare else None

    @staticmethod
    def _has_trauma(tags: dict[str, str]) -> bool:
        joined = ' '.join(
            filter(
                None,
                [
                    tags.get('name'),
                    tags.get('description'),
                    tags.get('healthcare:speciality'),
                ],
            )
        ).lower()
        return 'trauma' in joined

    @staticmethod
    def _has_icu(tags: dict[str, str]) -> bool:
        joined = ' '.join(filter(None, [tags.get('name'), tags.get('description')])).lower()
        return 'icu' in joined or tags.get('healthcare') == 'intensive_care'

    @staticmethod
    def _is_24hr(tags: dict[str, str]) -> bool:
        opening_hours = (tags.get('opening_hours') or '').lower()
        if not opening_hours:
            return True
        return '24/7' in opening_hours or '24 hours' in opening_hours

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius_m = 6371000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return radius_m * c

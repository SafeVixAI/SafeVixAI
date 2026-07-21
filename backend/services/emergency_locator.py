# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import logging
from collections.abc import Iterable
import json
import math
from pathlib import Path

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import Settings
from core.metrics import emergency_lookup_total
from core.redis_client import CacheHelper
from models.emergency import EmergencyService
from models.schemas import (
    EmergencyNumber,
    EmergencyNumbersResponse,
    EmergencyResponse,
    EmergencyServiceItem,
    SosResponse,
)
from services.exceptions import ExternalServiceError, ServiceValidationError
from services.local_emergency_catalog import LocalEmergencyEntry, load_local_emergency_catalog
from services.overpass_service import OverpassService

logger = logging.getLogger('uvicorn.emergency_locator')



SUPPORTED_CATEGORIES = {
    'hospital',
    'police',
    'ambulance',
    'fire',
    'towing',
    'pharmacy',
    'puncture',
    'showroom',
}

from services.city_center_repo import (
    _HARDCODED_CENTERS,
    _OFFLINE_CENTERS,
    get_all_city_centers,
    get_city_center,
    get_offline_centers,
)

# Backward-compatible aliases (used by scripts and tests).
# Prefer the repo functions for DB-backed lookups.
CITY_CENTERS: dict[str, tuple[float, float]] = dict(_HARDCODED_CENTERS)
OFFLINE_CITY_CENTERS: dict[str, tuple[float, float]] = dict(_OFFLINE_CENTERS)

DEFAULT_EMERGENCY_NUMBERS_DATA: dict[str, dict[str, str]] = {
    'national_emergency': {'service': '112', 'coverage': 'Pan-India', 'notes': 'Unified emergency response'},
    'ambulance': {'service': '102', 'coverage': 'Pan-India', 'notes': 'Public ambulance dispatch'},
    'police': {'service': '100', 'coverage': 'Pan-India', 'notes': 'Police control room'},
    'fire': {'service': '101', 'coverage': 'Pan-India', 'notes': 'Fire and rescue'},
    'medical_emergency': {'service': '108', 'coverage': 'Most states', 'notes': 'Integrated medical emergency response'},
    'state_highway': {'service': '1073', 'coverage': 'Many states', 'notes': 'State highway emergency helpline'},
    'health_helpline': {'service': '104', 'coverage': 'Many states', 'notes': 'Public health helpline'},
    'women_helpline': {'service': '1091', 'coverage': 'Pan-India', 'notes': 'Women safety helpline'},
    'child_helpline': {'service': '1098', 'coverage': 'Pan-India', 'notes': 'Child emergency support'},
    'disaster_management': {'service': '1099', 'coverage': 'Selected deployments', 'notes': 'Disaster management support'},
    'road_accident': {'service': '1033', 'coverage': 'National highways', 'notes': 'NHAI emergency helpline'},
    'aiims_trauma': {'service': '011-26588500', 'coverage': 'Delhi referral', 'notes': 'AIIMS Trauma Centre board line'},
    'cpgrams': {'service': '1800-11-0012', 'coverage': 'Pan-India', 'notes': 'Public grievance support desk'},
}


def _load_emergency_numbers() -> EmergencyNumbersResponse:
    project_root = Path(__file__).resolve().parents[2]
    candidate = project_root / 'chatbot_service' / 'data' / 'emergency_numbers.json'
    payload = DEFAULT_EMERGENCY_NUMBERS_DATA
    if candidate.exists():
        try:
            raw = json.loads(candidate.read_text(encoding='utf-8'))
            if isinstance(raw, dict) and isinstance(raw.get('numbers'), dict):
                payload = raw['numbers']
        except (json.JSONDecodeError, OSError, KeyError):
            payload = DEFAULT_EMERGENCY_NUMBERS_DATA
    return EmergencyNumbersResponse(
        numbers={
            key: EmergencyNumber(
                service=str(value.get('service') or '').strip(),
                coverage=str(value.get('coverage') or '').strip(),
                notes=str(value.get('notes')).strip() if value.get('notes') else None,
            )
            for key, value in payload.items()
            if isinstance(value, dict) and str(value.get('service') or '').strip()
        }
    )


EMERGENCY_NUMBERS = _load_emergency_numbers()


class EmergencyLocatorService:
    def __init__(self, *, settings: Settings, cache: CacheHelper, overpass_service: OverpassService) -> None:
        self.settings = settings
        self.cache = cache
        self.overpass_service = overpass_service
        self._local_catalog: list[LocalEmergencyEntry] | None = None

    def parse_categories(self, categories: str | Iterable[str] | None) -> list[str]:
        if categories is None:
            return ['hospital', 'police', 'ambulance', 'towing']
        if isinstance(categories, str):
            requested = [part.strip().lower() for part in categories.split(',') if part.strip()]
        else:
            requested = [str(part).strip().lower() for part in categories if str(part).strip()]
        normalized = [category for category in requested if category in SUPPORTED_CATEGORIES]
        return normalized or ['hospital', 'police', 'ambulance', 'towing']

    def build_radius_steps(self, radius: int | None = None) -> list[int]:
        if radius is None:
            return list(self.settings.emergency_radius_steps)
        capped = min(int(radius), self.settings.max_radius)
        steps = [step for step in self.settings.emergency_radius_steps if step <= capped]
        if not steps or steps[-1] != capped:
            steps.append(capped)
        return steps

    async def find_nearby(
        self,
        *,
        db: AsyncSession,
        lat: float,
        lon: float,
        categories: str | Iterable[str] | None,
        radius: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> EmergencyResponse:
        parsed_categories = self.parse_categories(categories)
        radius_steps = self.build_radius_steps(radius)
        cache_key = (
            f'emergency:nearby:{lat:.4f}:{lon:.4f}:{",".join(parsed_categories)}:'
            f'{radius_steps[-1]}:{limit}:{offset}'
        )
        cached = await self.cache.get_json(cache_key)
        if cached:
            return EmergencyResponse.model_validate(cached)

        try:
            response = await self._find_nearby_uncached(
                db=db,
                lat=lat,
                lon=lon,
                categories=parsed_categories,
                radius_steps=radius_steps,
                limit=limit,
                offset=offset,
            )
        except ExternalServiceError:
            stale = await self.cache.get_json_stale(cache_key)
            if stale is not None:
                logger.warning('Serving stale emergency cache for key=%s (live data unavailable)', cache_key)
                stale_response = EmergencyResponse.model_validate(stale)
                stale_response.source = 'stale_cache'
                return stale_response
            raise

        await self.cache.set_json(cache_key, response.model_dump(mode='json'), self.settings.cache_ttl_seconds)
        for cat in parsed_categories:
            emergency_lookup_total.labels(service_type=cat, source=response.source).inc()
        return response

    async def build_sos_payload(
        self,
        *,
        db: AsyncSession,
        lat: float,
        lon: float,
    ) -> SosResponse:
        nearby = await self.find_nearby(
            db=db,
            lat=lat,
            lon=lon,
            categories=['hospital', 'police', 'ambulance'],
            radius=self.settings.default_radius,
            limit=8,
        )
        return SosResponse(
            services=nearby.services,
            count=nearby.count,
            radius_used=nearby.radius_used,
            source=nearby.source,
            numbers=EMERGENCY_NUMBERS.numbers,
        )

    async def build_city_bundle(self, *, db: AsyncSession, city: str) -> dict:
        lookup_key = city.strip().lower()
        cache_key = f'offline:bundle:{lookup_key}'
        cached = await self.cache.get_json(cache_key)
        if cached:
            return cached
        center = CITY_CENTERS.get(lookup_key)
        if center is None:
            raise ServiceValidationError(f'Unknown offline bundle city: {city}')
        lat, lon = center
        categories = ['hospital', 'police', 'ambulance', 'fire', 'towing', 'pharmacy']
        database_items, _ = await self._query_database(
            db=db,
            lat=lat,
            lon=lon,
            categories=categories,
            radius_meters=self.settings.max_radius,
            limit=150,
        )
        services = list(database_items)
        source = 'database'

        local_items = self._search_local_catalog(
            lat=lat,
            lon=lon,
            categories=categories,
            radius_meters=self.settings.max_radius,
            limit=150,
        )
        if local_items:
            services = self._merge_results(services, local_items, 150)
            source = 'database+local' if database_items else 'local'

        if len(services) < 75:
            try:
                fallback = await self.overpass_service.search_services(
                    lat=lat,
                    lon=lon,
                    radius=self.settings.max_radius,
                    categories=categories,
                    limit=150,
                )
            except ExternalServiceError:
                fallback = []
            if fallback:
                services = self._merge_results(services, fallback, 150)
                source = f'{source}+overpass' if source != 'database' else ('database+overpass' if database_items else 'overpass')

        bundle = {
            'city': city,
            'center': {'lat': lat, 'lon': lon},
            'services': [item.model_dump(mode='json') for item in services],
            'numbers': EMERGENCY_NUMBERS.model_dump(mode='json')['numbers'],
            'source': source,
        }
        await self.cache.set_json(cache_key, bundle, self.settings.cache_ttl_seconds)
        return bundle

    async def _find_nearby_uncached(
        self,
        *,
        db: AsyncSession,
        lat: float,
        lon: float,
        categories: list[str],
        radius_steps: list[int],
        limit: int,
        offset: int = 0,
    ) -> EmergencyResponse:
        best: list[EmergencyServiceItem] = []
        best_radius = radius_steps[-1]
        source = 'database'
        database_items_count = 0
        total_items = 0

        for step in radius_steps:
            best, total_items = await self._query_database(
                db=db,
                lat=lat,
                lon=lon,
                categories=categories,
                radius_meters=step,
                limit=limit,
                offset=offset,
            )
            best_radius = step
            database_items_count = len(best)
            if len(best) >= self.settings.emergency_min_results:
                break

        if len(best) < self.settings.emergency_min_results and offset == 0:
            local_items = self._search_local_catalog(
                lat=lat,
                lon=lon,
                categories=categories,
                radius_meters=best_radius,
                limit=limit,
            )
            if local_items:
                best = self._merge_results(best, local_items, limit)
                source = 'database+local' if database_items_count else 'local'
                total_items += len(local_items)

        if len(best) < self.settings.emergency_min_results and offset == 0:
            try:
                fallback = await self.overpass_service.search_services(
                    lat=lat,
                    lon=lon,
                    radius=best_radius,
                    categories=categories,
                    limit=limit,
                )
            except ExternalServiceError:
                fallback = []
                if not best:
                    raise
            best = self._merge_results(best, fallback, limit)
            if fallback:
                if source == 'database':
                    source = 'database+overpass' if database_items_count else 'overpass'
                elif source == 'local':
                    source = 'local+overpass'
                elif source == 'database+local':
                    source = 'database+local+overpass'
                total_items += len(fallback)
            elif best and source == 'database':
                source = 'database'

        next_offset = offset + limit if (offset + limit) < total_items else None
        return EmergencyResponse(
            services=best,
            count=len(best),
            radius_used=best_radius,
            source=source,
            next_offset=next_offset,
            total_count=total_items,
        )

    async def _query_database(
        self,
        *,
        db: AsyncSession,
        lat: float,
        lon: float,
        categories: list[str],
        radius_meters: int,
        limit: int,
        offset: int = 0,
    ) -> tuple[list[EmergencyServiceItem], int]:
        point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        point_geography = cast(point, Geography)
        service_geography = cast(EmergencyService.location, Geography)
        distance_expr = func.ST_Distance(service_geography, point_geography).label('distance_meters')
        lat_expr = func.ST_Y(EmergencyService.location).label('lat')
        lon_expr = func.ST_X(EmergencyService.location).label('lon')

        stmt = (
            select(EmergencyService, lat_expr, lon_expr, distance_expr)
            .where(EmergencyService.category.in_(categories))
            .where(func.ST_DWithin(service_geography, point_geography, radius_meters))
            .order_by(EmergencyService.has_trauma.desc(), EmergencyService.is_24hr.desc(), distance_expr.asc())
            .offset(offset)
            .limit(limit)
        )

        count_stmt = (
            select(func.count(EmergencyService.id))
            .where(EmergencyService.category.in_(categories))
            .where(func.ST_DWithin(service_geography, point_geography, radius_meters))
        )
        total_count = (await db.execute(count_stmt)).scalar() or 0

        rows = (await db.execute(stmt)).all()
        items: list[EmergencyServiceItem] = []
        for service, item_lat, item_lon, distance in rows:
            items.append(
                EmergencyServiceItem(
                    id=str(service.id),
                    name=service.name,
                    category=service.category,
                    sub_category=service.sub_category,
                    phone=service.phone,
                    phone_emergency=service.phone_emergency,
                    lat=float(item_lat),
                    lon=float(item_lon),
                    distance_meters=float(distance),
                    has_trauma=service.has_trauma,
                    has_icu=service.has_icu,
                    is_24hr=service.is_24hr,
                    address=service.address,
                    source=service.source,
                )
            )
        return items, total_count

    def _get_local_catalog(self) -> list[LocalEmergencyEntry]:
        if self._local_catalog is None:
            project_root = Path(__file__).resolve().parents[2]
            self._local_catalog = load_local_emergency_catalog(project_root)
        return self._local_catalog

    def _search_local_catalog(
        self,
        *,
        lat: float,
        lon: float,
        categories: list[str],
        radius_meters: int,
        limit: int,
    ) -> list[EmergencyServiceItem]:
        items: list[EmergencyServiceItem] = []
        for entry in self._get_local_catalog():
            if entry.category not in categories:
                continue
            distance = self._distance_meters(lat, lon, entry.lat, entry.lon)
            if distance > radius_meters:
                continue
            items.append(self._entry_to_service_item(entry, distance))
        items.sort(key=lambda item: (0 if item.has_trauma else 1, 0 if item.is_24hr else 1, item.distance_meters))
        return items[:limit]

    @staticmethod
    def _entry_to_service_item(entry: LocalEmergencyEntry, distance_meters: float) -> EmergencyServiceItem:
        return EmergencyServiceItem(
            id=entry.id,
            name=entry.name,
            category=entry.category,
            sub_category=entry.sub_category,
            phone=entry.phone,
            phone_emergency=entry.phone_emergency,
            lat=entry.lat,
            lon=entry.lon,
            distance_meters=distance_meters,
            has_trauma=entry.has_trauma,
            has_icu=entry.has_icu,
            is_24hr=entry.is_24hr,
            address=entry.address,
            source=entry.source,
        )

    @staticmethod
    def _distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius = 6_371_000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = (
            math.sin(delta_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        )
        return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @staticmethod
    def _merge_results(
        database_items: list[EmergencyServiceItem],
        fallback_items: list[EmergencyServiceItem],
        limit: int,
    ) -> list[EmergencyServiceItem]:
        merged: list[EmergencyServiceItem] = list(database_items)
        seen = {
            (
                item.name.strip().lower(),
                item.category,
                round(item.lat, 4),
                round(item.lon, 4),
            )
            for item in database_items
        }
        for item in fallback_items:
            key = (item.name.strip().lower(), item.category, round(item.lat, 4), round(item.lon, 4))
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
            if len(merged) >= limit:
                break
        merged.sort(key=lambda item: (0 if item.has_trauma else 1, 0 if item.is_24hr else 1, item.distance_meters))
        return merged[:limit]

    # ── Public helper used by MCP tool ────────────────────────────────────────
    async def get_nearby_facilities(
        self,
        lat: float,
        lon: float,
        initial_radius: int = 5000,
    ) -> list[EmergencyServiceItem]:
        """Dynamic radius expansion: 5km → 15km → 25km.
        Returns results with confidence metadata in source field.
        Also queries Healthsites.io as a secondary source when Overpass returns < 5 results.
        """
        EXPANSION_STEPS = [initial_radius, 15000, 25000]
        all_results: list[EmergencyServiceItem] = []

        for radius in EXPANSION_STEPS:
            try:
                results = await self.overpass_service.search_services(
                    lat=lat,
                    lon=lon,
                    radius=radius,
                    categories=['hospital', 'police', 'ambulance', 'fire', 'pharmacy'],
                    limit=20,
                )
                # Merge local catalog
                local_items = self._search_local_catalog(
                    lat=lat,
                    lon=lon,
                    categories=['hospital', 'police', 'ambulance', 'fire', 'pharmacy'],
                    radius_meters=radius,
                    limit=20,
                )
                all_results = self._merge_results(results, local_items, 25)
                if len(all_results) >= 3:
                    break
            except ExternalServiceError:
                break

        # Secondary source: Healthsites.io — fills gaps Overpass misses
        if len(all_results) < 5:
            healthsites_items = await self._query_healthsites(lat=lat, lon=lon)
            all_results = self._merge_results(all_results, healthsites_items, 25)

        # Add confidence label to source field
        count = len(all_results)
        if count >= 5:
            confidence = "high"
        elif count >= 2:
            confidence = "moderate"
        elif count >= 1:
            confidence = "low"
        else:
            confidence = "offline"

        for item in all_results:
            item.source = f"{item.source}|confidence:{confidence}"

        return all_results

    async def _query_healthsites(self, *, lat: float, lon: float) -> list[EmergencyServiceItem]:
        """Query Healthsites.io API as a secondary emergency facility source.
        Covers India with 50,000+ facilities not always in OSM.
        """
        import httpx

        api_key = getattr(self.settings, 'healthsites_api_key', None)
        if not api_key:
            return []  # Skip gracefully if key not configured

        try:
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.get(
                    "https://healthsites.io/api/v2/facilities/",
                    params={
                        "api-key": api_key,
                        "format": "json",
                        "country": "IND",
                        "lat": lat,
                        "lng": lon,
                        "radius": 10,  # km
                        "limit": 10,
                    }
                )
                if not resp.is_success:
                    return []
                data = resp.json()

            items: list[EmergencyServiceItem] = []
            for facility in (data if isinstance(data, list) else data.get("results", [])):
                attributes = facility.get("attributes", {})
                geom = facility.get("geometry", {}).get("coordinates", [None, None])
                flon, flat = geom[0], geom[1]
                if flat is None or flon is None:
                    continue

                distance = self._distance_meters(lat, lon, float(flat), float(flon))
                name = attributes.get("name") or "Health Facility"
                amenity = (attributes.get("amenity") or "hospital").lower()

                items.append(EmergencyServiceItem(
                    id=f"healthsites-{facility.get('id', name)}",
                    name=name,
                    category="hospital" if "hospital" in amenity else "pharmacy",
                    sub_category=attributes.get("healthcare"),
                    phone=attributes.get("phone"),
                    phone_emergency=None,
                    lat=float(flat),
                    lon=float(flon),
                    distance_meters=distance,
                    has_trauma="trauma" in name.lower(),
                    has_icu="icu" in name.lower(),
                    is_24hr=attributes.get("opening_hours") == "24/7",
                    address=attributes.get("address"),
                    source="healthsites.io",
                ))
            return sorted(items, key=lambda x: x.distance_meters)[:10]

        except (httpx.HTTPError, json.JSONDecodeError, KeyError, TypeError):
            return []  # Always fail gracefully — Overpass is primary

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""OSM Bulk ingestor — fetches civic infrastructure from Overpass for ALL Indian cities."""

from __future__ import annotations

import logging
from typing import Any

from geoalchemy2 import WKTElement
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.osm_civic_feature import OSMCivicFeature
from services.civic_intel.base_ingestor import BaseIngestor

logger = logging.getLogger(__name__)

# Feature type → Overpass QL query fragment
CIVIC_FEATURE_QUERIES: dict[str, str] = {
    'streetlight': 'node["highway"="street_lamp"]',
    'traffic_signal': 'node["highway"="traffic_signals"]',
    'bus_stop': 'node["highway"="bus_stop"]',
    'speed_bump': 'node["traffic_calming"]',
    'cctv': 'node["man_made"="surveillance"]',
    'zebra_crossing': 'node["crossing"="zebra"]',
    'toll_booth': 'node["barrier"="toll_booth"]',
}

# Pan-India city bounding boxes (lat_south, lon_west, lat_north, lon_east)
# Phase 1 priority cities + top metros
CITY_BBOXES: dict[str, tuple[float, float, float, float]] = {
    # Maharashtra
    'Mumbai': (18.89, 72.77, 19.27, 72.99),
    'Pune': (18.41, 73.73, 18.64, 73.99),
    'Nagpur': (21.06, 79.01, 21.22, 79.16),
    # Tamil Nadu
    'Chennai': (12.88, 80.12, 13.23, 80.32),
    'Coimbatore': (10.93, 76.90, 11.10, 77.08),
    'Madurai': (9.87, 78.05, 9.98, 78.18),
    'Salem': (11.60, 78.08, 11.72, 78.22),
    'Tiruchirappalli': (10.75, 78.64, 10.87, 78.76),
    'Tirunelveli': (8.68, 77.65, 8.78, 77.78),
    'Vellore': (12.88, 79.09, 12.98, 79.18),
    # Andhra Pradesh
    'Visakhapatnam': (17.64, 83.16, 17.82, 83.42),
    'Vijayawada': (16.46, 80.57, 16.57, 80.70),
    'Guntur': (16.27, 80.40, 16.35, 80.50),
    'Nellore': (14.40, 79.94, 14.50, 80.04),
    'Kurnool': (15.79, 78.02, 15.87, 78.10),
    'Tirupati': (13.60, 79.36, 13.70, 79.46),
    'Kakinada': (16.93, 82.20, 17.02, 82.30),
    'Rajahmundry': (16.97, 81.73, 17.05, 81.83),
    # Karnataka
    'Bengaluru': (12.85, 77.46, 13.08, 77.78),
    'Mysuru': (12.25, 76.59, 12.38, 76.72),
    # Telangana
    'Hyderabad': (17.30, 78.35, 17.55, 78.60),
    # Delhi
    'Delhi': (28.40, 76.84, 28.88, 77.35),
    # West Bengal
    'Kolkata': (22.44, 88.25, 22.65, 88.45),
    # Uttar Pradesh
    'Lucknow': (26.76, 80.88, 26.95, 81.08),
    # Kerala
    'Kochi': (9.90, 76.22, 10.08, 76.38),
    'Thiruvananthapuram': (8.44, 76.88, 8.58, 77.02),
    # Rajasthan
    'Jaipur': (26.82, 75.72, 26.98, 75.88),
    # Gujarat
    'Ahmedabad': (22.95, 72.50, 23.12, 72.68),
    # Madhya Pradesh
    'Bhopal': (23.17, 77.33, 23.33, 77.52),
    # Punjab
    'Chandigarh': (30.68, 76.72, 30.80, 76.83),
}


class OSMBulkIngestor(BaseIngestor):
    """Queries Overpass API for civic features across pan-India cities."""

    def __init__(self, overpass_service: Any = None):
        self._overpass = overpass_service

    @property
    def name(self) -> str:
        return 'osm_civic'

    async def fetch(self) -> list[dict[str, Any]]:
        """Fetch civic features for all cities using Overpass API."""
        all_features: list[dict[str, Any]] = []

        for city, bbox in CITY_BBOXES.items():
            for feature_type, query_frag in CIVIC_FEATURE_QUERIES.items():
                try:
                    features = await self._query_overpass(city, bbox, feature_type, query_frag)
                    all_features.extend(features)
                except Exception as exc:
                    logger.warning('[OSM] %s/%s failed: %s', city, feature_type, exc)

            logger.info('[OSM] %s: fetched %d total features so far', city, len(all_features))

        return all_features

    async def _query_overpass(
        self, city: str, bbox: tuple, feature_type: str, query_frag: str,
    ) -> list[dict[str, Any]]:
        """Execute a single Overpass query for a city+feature_type."""
        south, west, north, east = bbox
        query = f"""
        [out:json][timeout:30];
        {query_frag}({south},{west},{north},{east});
        out body;
        """

        if self._overpass:
            # Use existing OverpassService if available
            data = await self._overpass._execute_query(query)
        else:
            resp = await self._fetch_with_retry(
                'https://overpass-api.de/api/interpreter',
                params={'data': query},
            )
            data = resp.json()

        elements = data.get('elements', [])
        return list(self.iter_parse_elements(elements, city, feature_type))

    def iter_parse_elements(self, elements: list[dict[str, Any]], city: str, feature_type: str) -> Any:
        """Iterative generator to parse OSM elements without large memory buffers."""
        for elem in elements:
            if elem.get('type') != 'node':
                continue
            lat, lon = elem.get('lat'), elem.get('lon')
            if lat is None or lon is None:
                continue
            yield {
                'osm_id': elem['id'],
                'feature_type': feature_type,
                'city': city,
                'lat': lat,
                'lon': lon,
                'tags_json': elem.get('tags', {}),
            }

    async def fetch_stream(self) -> Any:
        """Streaming iterative fetch yielding feature batches per city and feature type."""
        for city, bbox in CITY_BBOXES.items():
            for feature_type, query_frag in CIVIC_FEATURE_QUERIES.items():
                try:
                    features = await self._query_overpass(city, bbox, feature_type, query_frag)
                    if features:
                        yield features
                except Exception as exc:
                    logger.warning('[OSM] %s/%s stream failed: %s', city, feature_type, exc)

    async def transform(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Deduplicate by osm_id."""
        seen: set[int] = set()
        clean: list[dict[str, Any]] = []
        for r in raw:
            osm_id = r.get('osm_id')
            if osm_id and osm_id not in seen:
                seen.add(osm_id)
                clean.append(r)
        return clean

    async def load(
        self, db: AsyncSession, records: list[dict[str, Any]],
    ) -> tuple[int, int, int]:
        """Insert OSM civic features — skip existing by osm_id + feature_type."""
        inserted, updated, skipped = 0, 0, 0

        for record in records:
            try:
                wkt = f"POINT({record['lon']} {record['lat']})"
                stmt = pg_insert(OSMCivicFeature).values(
                    osm_id=record['osm_id'],
                    feature_type=record['feature_type'],
                    city=record.get('city'),
                    location=WKTElement(wkt, srid=4326),
                    tags_json=record.get('tags_json', {}),
                )
                stmt = stmt.on_conflict_do_nothing()
                result = await db.execute(stmt)
                if result.rowcount > 0:
                    inserted += 1
                else:
                    skipped += 1
            except Exception as exc:
                logger.debug('[OSM] Skip osm_id=%s: %s', record.get('osm_id'), exc)
                skipped += 1

        return inserted, updated, skipped

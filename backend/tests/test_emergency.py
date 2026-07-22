# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from fastapi.testclient import TestClient

from core.redis_client import CacheHelper
from models.schemas import EmergencyResponse, EmergencyServiceItem, SosResponse
from services.emergency_locator import EmergencyLocatorService
from services.exceptions import ExternalServiceError
from services.local_emergency_catalog import LocalEmergencyEntry


class FakeCache:
    def __init__(self) -> None:
        self.store: dict[str, object] = {}
        self.backend_name = 'memory'

    async def get_json(self, key: str):
        return self.store.get(key)

    async def set_json(self, key: str, value, ttl_seconds: int) -> None:
        self.store[key] = value

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        return None


class FakeOverpass:
    async def search_services(self, *, lat: float, lon: float, radius: int, categories: list[str], limit: int):
        return [
            EmergencyServiceItem(
                id='osm-1',
                name='Fallback General Hospital',
                category='hospital',
                lat=lat + 0.001,
                lon=lon + 0.001,
                distance_meters=180.0,
                has_trauma=True,
                is_24hr=True,
                source='overpass',
            )
        ]


class FakeEmergencyApiService:
    async def find_nearby(self, **kwargs) -> EmergencyResponse:
        return EmergencyResponse(
            services=[
                EmergencyServiceItem(
                    id='1',
                    name='City Hospital',
                    category='hospital',
                    lat=13.08,
                    lon=80.27,
                    distance_meters=245.0,
                    has_trauma=True,
                    is_24hr=True,
                )
            ],
            count=1,
            radius_used=1000,
            source='database',
        )

    async def build_sos_payload(self, **kwargs) -> SosResponse:
        nearby = await self.find_nearby()
        return SosResponse(
            services=nearby.services,
            count=nearby.count,
            radius_used=nearby.radius_used,
            source=nearby.source,
            numbers={
                'national_emergency': {
                    'service': '112',
                    'coverage': 'Pan-India',
                    'notes': 'Unified emergency response',
                }
            },
        )


def test_health_endpoint_returns_stable_response(app, monkeypatch):
    async def fake_check_database() -> bool:
        return True

    monkeypatch.setattr('main.check_database', fake_check_database)
    with TestClient(app) as client:
        client.app.state.cache = FakeCache()
        response = client.get('/health')

    assert response.status_code == 200
    body = response.json()
    payload = body.get("data", body)
    assert payload['status'] == 'ok'
    assert payload['database_available'] is True
    assert payload['chatbot_mode'] == 'external_service'
    assert isinstance(payload['chatbot_ready'], bool)
    assert payload['cache_available'] is True
    assert payload['cache_backend'] == 'memory'


def test_emergency_numbers_endpoint(app):
    with TestClient(app) as client:
        response = client.get('/api/v1/emergency/numbers')

    assert response.status_code == 200
    body = response.json()
    payload = body.get("data", body)
    assert payload['numbers']['national_emergency']['service'] == '112'
    assert payload['numbers']['national_highway']['service'] == '1033'


def test_nearby_endpoint_uses_api_service(app):
    with TestClient(app) as client:
        client.app.state.emergency_service = FakeEmergencyApiService()
        response = client.get('/api/v1/emergency/nearby?lat=13.0827&lon=80.2707&categories=hospital')

    assert response.status_code == 200
    body = response.json()
    payload = body.get("data", body)
    assert payload['count'] == 1
    assert payload['services'][0]['name'] == 'City Hospital'
    assert payload['radius_used'] == 1000


def test_emergency_locator_expands_radius_and_merges_overpass():
    class Settings:
        emergency_radius_steps = [500, 1000, 5000]
        max_radius = 5000
        emergency_min_results = 2
        cache_ttl_seconds = 60
        default_radius = 5000

    cache = FakeCache()
    service = EmergencyLocatorService(settings=Settings(), cache=cache, overpass_service=FakeOverpass())

    async def fake_query_database(*, radius_meters: int, **kwargs):
        if radius_meters == 500:
            return [], 0
        items = [
            EmergencyServiceItem(
                id='db-1',
                name='Database Police Station',
                category='police',
                lat=13.081,
                lon=80.271,
                distance_meters=120.0,
                is_24hr=True,
                source='database',
            )
        ]
        return items, len(items)

    service._query_database = fake_query_database  # type: ignore[method-assign]

    import asyncio

    result = asyncio.run(
        service.find_nearby(
            db=object(),
            lat=13.0827,
            lon=80.2707,
            categories='hospital,police',
            radius=5000,
            limit=5,
        )
    )

    assert result.radius_used == 5000
    assert result.source == 'database+local'
    assert result.count == 5
    assert {item.source for item in result.services} == {'database', 'local:police_stations'}


def test_emergency_locator_returns_database_results_when_overpass_fails():
    class Settings:
        emergency_radius_steps = [500, 1000, 5000]
        max_radius = 5000
        emergency_min_results = 2
        cache_ttl_seconds = 60
        default_radius = 5000

    class FailingOverpass:
        async def search_services(self, **kwargs):
            raise ExternalServiceError('Overpass API unavailable')

    cache = FakeCache()
    service = EmergencyLocatorService(settings=Settings(), cache=cache, overpass_service=FailingOverpass())

    async def fake_query_database(*, radius_meters: int, **kwargs):
        if radius_meters < 5000:
            return [], 0
        items = [
            EmergencyServiceItem(
                id='db-1',
                name='Database Police Station',
                category='police',
                lat=13.081,
                lon=80.271,
                distance_meters=120.0,
                is_24hr=True,
                source='database',
            )
        ]
        return items, len(items)

    service._query_database = fake_query_database  # type: ignore[method-assign]

    import asyncio

    result = asyncio.run(
        service.find_nearby(
            db=object(),
            lat=13.0827,
            lon=80.2707,
            categories='police',
            radius=5000,
            limit=5,
        )
    )

    assert result.source == 'database+local'
    assert result.count == 5
    assert any(s.name == 'Database Police Station' for s in result.services)


def test_cache_helper_falls_back_to_memory():
    import asyncio

    cache = CacheHelper()

    async def round_trip():
        await cache.set_json('demo', {'ok': True}, 60)
        return await cache.get_json('demo')

    assert asyncio.run(round_trip()) == {'ok': True}
    assert cache.backend_name == 'memory'


def test_emergency_locator_uses_local_catalog_before_overpass():
    class Settings:
        emergency_radius_steps = [500, 1000, 5000]
        max_radius = 5000
        emergency_min_results = 2
        cache_ttl_seconds = 60
        default_radius = 5000

    class FailingOverpass:
        async def search_services(self, **kwargs):
            raise ExternalServiceError('Overpass API unavailable')

    cache = FakeCache()
    service = EmergencyLocatorService(settings=Settings(), cache=cache, overpass_service=FailingOverpass())
    service._local_catalog = [
        LocalEmergencyEntry(
            id='local-1',
            name='Local Trauma Hospital',
            category='hospital',
            lat=13.0830,
            lon=80.2709,
            has_trauma=True,
            source='local:hospital_directory',
        )
    ]

    async def fake_query_database(*, radius_meters: int, **kwargs):
        return [], 0

    service._query_database = fake_query_database  # type: ignore[method-assign]

    import asyncio

    result = asyncio.run(
        service.find_nearby(
            db=object(),
            lat=13.0827,
            lon=80.2707,
            categories='hospital',
            radius=5000,
            limit=5,
        )
    )

    assert result.source == 'local'
    assert result.count == 1
    assert result.services[0].name == 'Local Trauma Hospital'

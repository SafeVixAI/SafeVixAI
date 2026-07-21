# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from core.config import Settings
from core.redis_client import CacheHelper
from models.schemas import (
    AuthorityPreviewResponse,
    RoadInfrastructureResponse,
    RoadIssuesResponse,
    RoadIssueItem,
    RoadReportResponse,
)
from services.authority_router import AuthorityRouter
from services.exceptions import ExternalServiceError
from services.roadwatch_service import RoadWatchService


class FakeRoadwatchService:
    async def get_authority(self, **kwargs) -> AuthorityPreviewResponse:
        return AuthorityPreviewResponse(
            road_type='National Highway',
            road_type_code='NH',
            road_name='Grand Southern Trunk Road',
            road_number='NH32',
            authority_name='NHAI',
            helpline='1033',
            complaint_portal='https://nhai.gov.in/complaint',
            escalation_path='Ministry of Road Transport',
            source='road_infrastructure',
        )

    async def get_infrastructure(self, **kwargs) -> RoadInfrastructureResponse:
        return RoadInfrastructureResponse(
            road_type='National Highway',
            road_type_code='NH',
            road_name='Grand Southern Trunk Road',
            road_number='NH32',
            contractor_name='ABC Infra',
            exec_engineer='R. Kumar',
            exec_engineer_phone='9000000001',
            budget_sanctioned=50000000,
            budget_spent=32000000,
            source='road_infrastructure',
        )

    async def find_nearby_issues(self, **kwargs) -> RoadIssuesResponse:
        return RoadIssuesResponse(
            issues=[
                RoadIssueItem(
                    uuid=uuid4(),
                    issue_type='pothole',
                    severity=4,
                    description='Large pothole near signal',
                    lat=13.04,
                    lon=80.25,
                    location_address='GST Road, Chennai',
                    road_name='GST Road',
                    road_type='National Highway',
                    road_number='NH32',
                    authority_name='NHAI',
                    status='open',
                    created_at='2026-04-05T10:00:00',  # type: ignore[arg-type]
                    distance_meters=84.5,
                )
            ],
            count=1,
            radius_used=5000,
        )

    async def submit_report(self, **kwargs) -> RoadReportResponse:
        return RoadReportResponse(
            uuid=uuid4(),
            complaint_ref='RS-TEST-0001',
            authority_name='NHAI',
            authority_phone='1033',
            complaint_portal='https://nhai.gov.in/complaint',
            road_type='National Highway',
            road_type_code='NH',
            road_number='NH32',
            road_name='Grand Southern Trunk Road',
            contractor_name='ABC Infra',
            status='open',
        )


def test_authority_endpoint(app):
    with TestClient(app) as client:
        client.app.state.roadwatch_service = FakeRoadwatchService()
        response = client.get('/api/v1/roads/authority?lat=13.04&lon=80.25')

    assert response.status_code == 200
    payload = response.json()
    assert payload['data']['authority_name'] == 'NHAI'
    assert payload['data']['road_type_code'] == 'NH'


def test_infrastructure_endpoint(app):
    with TestClient(app) as client:
        client.app.state.roadwatch_service = FakeRoadwatchService()
        response = client.get('/api/v1/roads/infrastructure?lat=13.04&lon=80.25')

    assert response.status_code == 200
    payload = response.json()
    assert payload['data']['contractor_name'] == 'ABC Infra'
    assert payload['data']['source'] == 'road_infrastructure'


def test_nearby_issues_endpoint(app):
    with TestClient(app) as client:
        client.app.state.roadwatch_service = FakeRoadwatchService()
        response = client.get('/api/v1/roads/issues?lat=13.04&lon=80.25&radius=5000')

    assert response.status_code == 200
    payload = response.json()
    assert payload['data']['count'] == 1
    assert payload['data']['issues'][0]['issue_type'] == 'pothole'


def test_submit_report_endpoint(app):
    with TestClient(app) as client:
        client.app.state.roadwatch_service = FakeRoadwatchService()
        response = client.post(
            '/api/v1/roads/report',
            data={
                'lat': '13.04',
                'lon': '80.25',
                'issue_type': 'pothole',
                'severity': '4',
                'description': 'Large pothole near signal',
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload['data']['authority_name'] == 'NHAI'
    assert payload['data']['status'] == 'open'
    assert payload['data']['complaint_ref'] == 'RS-TEST-0001'


def test_nearby_issues_rejects_invalid_status(app):
    with TestClient(app) as client:
        client.app.state.roadwatch_service = FakeRoadwatchService()
        response = client.get('/api/v1/roads/issues?lat=13.04&lon=80.25&statuses=open,broken')

    assert response.status_code == 422
    assert 'Unsupported statuses' in response.json()['detail']


def test_authority_router_normalizes_road_types():
    assert AuthorityRouter.normalize_road_type('State Highway', 'SH49') == 'SH'

    assert AuthorityRouter.normalize_road_type('Village Road', None) == 'VILLAGE'

    assert AuthorityRouter.normalize_road_type('National Highway', 'NH32') == 'NH'
class DummyDbResult:
    def scalar(self):
        return 0
    def scalar_one_or_none(self):
        return None
    def scalars(self):
        return self
    def all(self):
        return []
    def first(self):
        return None


class DummyDbSession:
    def __init__(self) -> None:
        self.added = None
        self.added_list = []

    def add(self, obj) -> None:
        self.added_list.append(obj)
        if hasattr(obj, 'location_address') or getattr(obj, '__tablename__', None) == 'road_issues':
            self.added = obj
        elif not self.added:
            self.added = obj

    async def execute(self, stmt) -> DummyDbResult:
        return DummyDbResult()

    async def commit(self) -> None:
        return None

    async def refresh(self, obj) -> None:
        return None


class FailingOverpassService:
    async def get_road_context(self, **kwargs):
        raise ExternalServiceError('Overpass unavailable')


class StaticAuthorityResolver:
    async def resolve(self, **kwargs) -> AuthorityPreviewResponse:
        return AuthorityPreviewResponse(
            road_type='Urban Road',
            road_type_code='URBAN',
            authority_name='Municipal Corporation',
            helpline='1800-11-0012',
            complaint_portal='https://pgportal.gov.in',
            escalation_path='Municipal Commissioner',
            source='fallback',
        )


class FailingGeocodingService:
    async def reverse(self, **kwargs):
        raise ExternalServiceError('Nominatim unavailable')


@pytest.mark.asyncio
async def test_authority_router_falls_back_when_overpass_unavailable():
    router = AuthorityRouter(
        settings=Settings(),
        overpass_service=FailingOverpassService(),
        cache=CacheHelper(),
    )

    async def no_infrastructure(**kwargs):
        return None

    router._lookup_infrastructure = no_infrastructure  # type: ignore[method-assign]

    result = await router.resolve(db=DummyDbSession(), lat=13.04, lon=80.25)

    assert result.source == 'fallback'
    assert result.authority_name == 'Municipal Corporation'
    assert result.road_type_code == 'URBAN'


@pytest.mark.asyncio
async def test_submit_report_survives_geocoding_failure():
    service = RoadWatchService(
        settings=Settings(),
        cache=CacheHelper(),
        geocoding_service=FailingGeocodingService(),
        authority_router=StaticAuthorityResolver(),
    )
    db = DummyDbSession()

    response = await service.submit_report(
        db=db,
        lat=13.04,
        lon=80.25,
        issue_type='pothole',
        severity=3,
        description='Fresh pothole near junction',
        photo=None,
    )

    assert response.status == 'open'
    assert response.authority_name == 'Municipal Corporation'
    assert db.added is not None
    assert db.added.location_address is None

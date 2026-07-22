# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from core.config import Settings
from core.redis_client import CacheHelper
from models.road_issue import RoadInfrastructure
from models.schemas import AuthorityPreviewResponse
from services.authority_router import (
    AUTHORITY_MATRIX,
    ROAD_TYPE_LABELS,
    AuthorityInfo,
    AuthorityRouter,
)
from services.exceptions import ExternalServiceError
from services.overpass_service import OverpassService, RoadContext


@pytest.fixture
def settings() -> MagicMock:
    return MagicMock(spec=Settings)


@pytest.fixture
def overpass_service() -> AsyncMock:
    return AsyncMock(spec=OverpassService)


@pytest.fixture
def cache() -> MagicMock:
    return MagicMock(spec=CacheHelper)


@pytest.fixture
def router(settings: MagicMock, overpass_service: AsyncMock, cache: MagicMock) -> AuthorityRouter:
    return AuthorityRouter(settings=settings, overpass_service=overpass_service, cache=cache)


@pytest.fixture
def db() -> AsyncMock:
    m = AsyncMock()
    m.execute = AsyncMock()
    return m


def _make_infrastructure(**kwargs) -> MagicMock:
    infra = MagicMock(spec=RoadInfrastructure)
    for k, v in kwargs.items():
        setattr(infra, k, v)
    return infra


# ── AuthorityInfo dataclass ────────────────────────────────────────────────


class TestAuthorityInfo:
    def test_fields(self) -> None:
        info = AuthorityInfo(
            authority_name='NHAI',
            helpline='1033',
            complaint_portal='https://nhai.gov.in/complaint',
            escalation_path='Ministry of Road Transport',
        )
        assert info.authority_name == 'NHAI'
        assert info.helpline == '1033'
        assert info.complaint_portal == 'https://nhai.gov.in/complaint'
        assert info.escalation_path == 'Ministry of Road Transport'

    def test_is_frozen(self) -> None:
        info = AuthorityInfo('NHAI', '1033', 'https://nhai.gov.in', 'MoRTH')
        with pytest.raises(AttributeError):
            info.authority_name = 'State PWD'


# ── AUTHORITY_MATRIX ───────────────────────────────────────────────────────


class TestAuthorityMatrix:
    def test_has_all_five_keys(self) -> None:
        assert set(AUTHORITY_MATRIX.keys()) == {'NH', 'SH', 'MDR', 'VILLAGE', 'URBAN'}

    def test_nh_helpline(self) -> None:
        assert AUTHORITY_MATRIX['NH'].helpline == '1033'

    def test_sh_helpline(self) -> None:
        assert AUTHORITY_MATRIX['SH'].helpline == '1800-180-6763'

    def test_mdr_helpline(self) -> None:
        assert AUTHORITY_MATRIX['MDR'].helpline == '1076'

    def test_village_helpline(self) -> None:
        assert AUTHORITY_MATRIX['VILLAGE'].helpline == '1800-180-6763'

    def test_urban_helpline(self) -> None:
        assert AUTHORITY_MATRIX['URBAN'].helpline == '1800-11-0012'

    def test_all_are_authority_info(self) -> None:
        for v in AUTHORITY_MATRIX.values():
            assert isinstance(v, AuthorityInfo)


# ── ROAD_TYPE_LABELS ───────────────────────────────────────────────────────


class TestRoadTypeLabels:
    def test_has_all_five_codes(self) -> None:
        assert set(ROAD_TYPE_LABELS.keys()) == {'NH', 'SH', 'MDR', 'VILLAGE', 'URBAN'}

    def test_nh_label(self) -> None:
        assert ROAD_TYPE_LABELS['NH'] == 'National Highway'

    def test_sh_label(self) -> None:
        assert ROAD_TYPE_LABELS['SH'] == 'State Highway'

    def test_mdr_label(self) -> None:
        assert ROAD_TYPE_LABELS['MDR'] == 'Major District Road'

    def test_village_label(self) -> None:
        assert ROAD_TYPE_LABELS['VILLAGE'] == 'Village Road'

    def test_urban_label(self) -> None:
        assert ROAD_TYPE_LABELS['URBAN'] == 'Urban Road'


# ── Constructor ────────────────────────────────────────────────────────────


class TestConstructor:
    def test_stores_dependencies(self, settings: MagicMock, overpass_service: AsyncMock, cache: MagicMock) -> None:
        router = AuthorityRouter(settings=settings, overpass_service=overpass_service, cache=cache)
        assert router.settings is settings
        assert router.overpass_service is overpass_service
        assert router.cache is cache


# ── _lookup_infrastructure ─────────────────────────────────────────────────


class TestLookupInfrastructure:
    async def test_returns_infrastructure_when_found(self, router: AuthorityRouter) -> None:
        db = AsyncMock()
        db.execute = AsyncMock()
        expected = _make_infrastructure(road_type='NH', road_number='NH-48')
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = expected
        db.execute.return_value = result_mock

        result = await router._lookup_infrastructure(db=db, lat=13.0, lon=80.0)

        assert result is expected
        db.execute.assert_awaited_once()

    async def test_returns_none_when_not_found(self, router: AuthorityRouter) -> None:
        db = AsyncMock()
        db.execute = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        result = await router._lookup_infrastructure(db=db, lat=13.0, lon=80.0)

        assert result is None


# ── _from_road_context ─────────────────────────────────────────────────────


class TestFromRoadContext:
    def test_builds_response_with_authority_info(self, router: AuthorityRouter) -> None:
        ctx = RoadContext(
            road_type_code='NH',
            road_type='National Highway',
            road_name='GT Road',
            road_number='NH-48',
            tags={},
            distance_meters=10.0,
        )

        result = router._from_road_context(ctx)

        assert isinstance(result, AuthorityPreviewResponse)
        assert result.road_type == 'National Highway'
        assert result.road_type_code == 'NH'
        assert result.road_name == 'GT Road'
        assert result.road_number == 'NH-48'
        assert result.authority_name == 'NHAI'
        assert result.helpline == '1033'
        assert result.complaint_portal == 'https://nhai.gov.in/complaint'
        assert result.escalation_path == 'Ministry of Road Transport'
        assert result.source == 'overpass'

    def test_builds_response_with_sh_authority(self, router: AuthorityRouter) -> None:
        ctx = RoadContext(
            road_type_code='SH',
            road_type='State Highway',
            road_name=None,
            road_number='SH-1',
            tags={},
            distance_meters=5.0,
        )

        result = router._from_road_context(ctx)

        assert result.road_type_code == 'SH'
        assert result.authority_name == 'State PWD'
        assert result.helpline == '1800-180-6763'
        assert result.source == 'overpass'
        assert result.road_name is None

    def test_builds_response_with_mdr_authority(self, router: AuthorityRouter) -> None:
        ctx = RoadContext(
            road_type_code='MDR',
            road_type='Major District Road',
            road_name='District Road 12',
            road_number=None,
            tags={'surface': 'asphalt'},
            distance_meters=20.0,
        )

        result = router._from_road_context(ctx)

        assert result.road_type_code == 'MDR'
        assert result.authority_name == 'District Collector / DRDA'
        assert result.helpline == '1076'
        assert result.source == 'overpass'


# ── _fallback_preview ──────────────────────────────────────────────────────


class TestFallbackPreview:
    def test_returns_urban_with_fallback_source(self, router: AuthorityRouter) -> None:
        result = router._fallback_preview()

        assert isinstance(result, AuthorityPreviewResponse)
        assert result.road_type == 'Urban Road'
        assert result.road_type_code == 'URBAN'
        assert result.authority_name == 'Municipal Corporation'
        assert result.helpline == '1800-11-0012'
        assert result.complaint_portal == 'https://pgportal.gov.in'
        assert result.escalation_path == 'Municipal Commissioner'
        assert result.source == 'fallback'
        assert result.road_name is None
        assert result.road_number is None
        assert result.exec_engineer is None
        assert result.exec_engineer_phone is None
        assert result.contractor_name is None
        assert result.budget_sanctioned is None
        assert result.budget_spent is None
        assert result.last_relayed_date is None
        assert result.next_maintenance is None
        assert result.data_source_url is None


# ── resolve ────────────────────────────────────────────────────────────────


class TestResolve:
    async def test_infrastructure_found_returns_from_db(
        self, router: AuthorityRouter, db: AsyncMock,
    ) -> None:
        infra = _make_infrastructure(
            road_type='NH',
            road_number='NH-48',
            road_name='GT Road',
            exec_engineer='A. Kumar',
            exec_engineer_phone='9999999999',
            contractor_name='XYZ Constructions',
            budget_sanctioned=50000000,
            budget_spent=30000000,
            last_relayed_date=None,
            next_maintenance=None,
            data_source_url='https://data.gov.in/road/123',
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = infra
        db.execute.return_value = result_mock

        result = await router.resolve(db=db, lat=13.0, lon=80.0)

        assert isinstance(result, AuthorityPreviewResponse)
        assert result.road_type == 'National Highway'
        assert result.road_type_code == 'NH'
        assert result.road_name == 'GT Road'
        assert result.road_number == 'NH-48'
        assert result.authority_name == 'NHAI'
        assert result.helpline == '1033'
        assert result.exec_engineer == 'A. Kumar'
        assert result.exec_engineer_phone == '9999999999'
        assert result.contractor_name == 'XYZ Constructions'
        assert result.budget_sanctioned == 50000000
        assert result.budget_spent == 30000000
        assert result.data_source_url == 'https://data.gov.in/road/123'
        assert result.source == 'road_infrastructure'

    async def test_infrastructure_not_found_overpass_succeeds(
        self, router: AuthorityRouter, db: AsyncMock,
    ) -> None:
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        ctx = RoadContext(
            road_type_code='SH',
            road_type='State Highway',
            road_name='State Road 42',
            road_number='SH-42',
            tags={},
            distance_meters=15.0,
        )
        router.overpass_service.get_road_context = AsyncMock(return_value=ctx)

        result = await router.resolve(db=db, lat=13.0, lon=80.0)

        assert result.road_type == 'State Highway'
        assert result.road_type_code == 'SH'
        assert result.road_name == 'State Road 42'
        assert result.road_number == 'SH-42'
        assert result.source == 'overpass'
        router.overpass_service.get_road_context.assert_awaited_once_with(lat=13.0, lon=80.0)

    async def test_overpass_raises_exception_returns_fallback(
        self, router: AuthorityRouter, db: AsyncMock,
    ) -> None:
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock
        router.overpass_service.get_road_context = AsyncMock(
            side_effect=ExternalServiceError('Overpass unavailable'),
        )

        result = await router.resolve(db=db, lat=13.0, lon=80.0)

        assert result.road_type_code == 'URBAN'
        assert result.source == 'fallback'

    async def test_overpass_returns_none_returns_fallback(
        self, router: AuthorityRouter, db: AsyncMock,
    ) -> None:
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock
        router.overpass_service.get_road_context = AsyncMock(return_value=None)

        result = await router.resolve(db=db, lat=13.0, lon=80.0)

        assert result.road_type_code == 'URBAN'
        assert result.source == 'fallback'


# ── normalize_road_type ────────────────────────────────────────────────────


class TestNormalizeRoadType:
    def test_nh_exact(self) -> None:
        assert AuthorityRouter.normalize_road_type('NH', None) == 'NH'

    def test_sh_full_name(self) -> None:
        assert AuthorityRouter.normalize_road_type('State Highway', None) == 'SH'

    def test_mdr_exact(self) -> None:
        assert AuthorityRouter.normalize_road_type('MDR', None) == 'MDR'

    def test_village_full_name(self) -> None:
        assert AuthorityRouter.normalize_road_type('Village Road', None) == 'VILLAGE'

    def test_pmgsy_returns_village(self) -> None:
        assert AuthorityRouter.normalize_road_type('PMGSY', None) == 'VILLAGE'

    def test_unknown_returns_urban(self) -> None:
        assert AuthorityRouter.normalize_road_type('Something else', None) == 'URBAN'

    def test_none_returns_urban(self) -> None:
        assert AuthorityRouter.normalize_road_type(None, None) == 'URBAN'

    def test_road_number_contains_nh(self) -> None:
        assert AuthorityRouter.normalize_road_type(None, 'NH-48') == 'NH'

    def test_nh_in_long_string(self) -> None:
        assert AuthorityRouter.normalize_road_type('NH Road Sector 5', None) == 'NH'

    def test_sh_abbreviation(self) -> None:
        assert AuthorityRouter.normalize_road_type('SH', None) == 'SH'

    def test_sh_road_number(self) -> None:
        assert AuthorityRouter.normalize_road_type(None, 'SH-5') == 'SH'

    def test_district_returns_mdr(self) -> None:
        assert AuthorityRouter.normalize_road_type('DISTRICT', None) == 'MDR'

    def test_mdr_road_number(self) -> None:
        assert AuthorityRouter.normalize_road_type(None, 'MDR-101') == 'MDR'

    def test_lowercase_nh(self) -> None:
        assert AuthorityRouter.normalize_road_type('nh', None) == 'NH'

    def test_lowercase_sh_road_number(self) -> None:
        assert AuthorityRouter.normalize_road_type(None, 'sh-22') == 'SH'

    def test_village_lowercase(self) -> None:
        assert AuthorityRouter.normalize_road_type('village road', None) == 'VILLAGE'

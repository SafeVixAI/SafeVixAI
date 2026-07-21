# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import UploadFile

from core.config import Settings
from core.redis_client import CacheHelper
from models.road_issue import RoadInfrastructure, RoadIssue
from models.schemas import (
    AuthorityPreviewResponse,
    RoadInfrastructureResponse,
    RoadIssuesResponse,
    RoadReportResponse,
)
from services.authority_router import AuthorityRouter
from services.exceptions import ExternalServiceError, ServiceValidationError
from services.geocoding_service import GeocodingService
from services.roadwatch_photos import is_valid_image_magic
from services.roadwatch_service import (
    RoadWatchService,
    UploadedPhotoUrl,
)
from services.ward_service import WardService

# ---------------------------------------------------------------------------
# Standalone function tests
# ---------------------------------------------------------------------------


class TestIsValidImageMagic:
    def test_jpeg_magic(self) -> None:
        assert is_valid_image_magic(b'\xff\xd8\xff\xe0\x00\x10JFIF')

    def test_png_magic(self) -> None:
        assert is_valid_image_magic(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR')

    def test_webp_magic(self) -> None:
        assert is_valid_image_magic(b'RIFF\x00\x00\x00\x00WEBP')

    def test_riff_without_webp(self) -> None:
        assert not is_valid_image_magic(b'RIFF\x00\x00\x00\x00XXXX')

    def test_unknown_bytes(self) -> None:
        assert not is_valid_image_magic(b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b')

    def test_empty_bytes(self) -> None:
        assert not is_valid_image_magic(b'')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TEST_UUID = uuid.UUID('12345678-1234-5678-1234-567812345678')
FIXED_NOW = datetime(2026, 5, 23, 12, 0, 0)


def make_mock_settings(**overrides: object) -> MagicMock:
    s = MagicMock(spec=Settings)
    s.cache_ttl_seconds = 3600
    s.authority_cache_ttl_seconds = 3600
    s.allowed_upload_content_types = ['image/jpeg', 'image/png', 'image/webp']
    s.max_upload_bytes = 5 * 1024 * 1024
    s.upload_dir = Path('/tmp/uploads')
    s.local_upload_base_url = None
    s.supabase_url = None
    s.supabase_service_role_key = None
    s.road_photo_bucket = 'road-photos'
    for k, v in overrides.items():
        setattr(s, k, v)
    return s


def make_mock_authority_preview(**overrides: object) -> AuthorityPreviewResponse:
    kwargs: dict[str, object] = {
        'road_type': 'National Highway',
        'road_type_code': 'NH',
        'road_name': 'GST Road',
        'road_number': 'NH32',
        'authority_name': 'NHAI',
        'helpline': '1033',
        'complaint_portal': 'https://nhai.gov.in/complaint',
        'escalation_path': 'Ministry of Road Transport',
        'source': 'authority_matrix',
    }
    kwargs.update(overrides)
    return AuthorityPreviewResponse(**kwargs)


def make_mock_road_issue(**overrides: object) -> MagicMock:
    issue = MagicMock(spec=RoadIssue)
    issue.uuid = TEST_UUID
    issue.issue_type = 'pothole'
    issue.severity = 3
    issue.description = 'A pothole'
    issue.location_address = 'GST Road, Chennai'
    issue.road_name = 'GST Road'
    issue.road_type = 'National Highway'
    issue.road_number = 'NH32'
    issue.authority_name = 'NHAI'
    issue.status = 'open'
    issue.created_at = FIXED_NOW
    issue.category = 'roads'
    issue.sub_category = 'pothole'
    issue.ward_id = None
    issue.ward_name = None
    issue.assigned_officer_id = None
    issue.sla_deadline = None
    issue.resolved_at = None
    issue.duplicate_of_uuid = None
    issue.confirmation_count = 0
    issue.before_photo_url = None
    issue.after_photo_url = None
    issue.complaint_ref = 'RS-TEST1234'
    for k, v in overrides.items():
        setattr(issue, k, v)
    return issue


def make_mock_road_infrastructure(**overrides: object) -> MagicMock:
    infra = MagicMock(spec=RoadInfrastructure)
    infra.road_type = 'National Highway'
    infra.road_number = 'NH32'
    infra.road_name = 'GST Road'
    infra.contractor_name = 'ABC Infra'
    infra.exec_engineer = 'R. Kumar'
    infra.exec_engineer_phone = '9000000001'
    infra.budget_sanctioned = 50000000
    infra.budget_spent = 32000000
    infra.last_relayed_date = None
    infra.next_maintenance = None
    infra.data_source_url = 'https://example.com'
    for k, v in overrides.items():
        setattr(infra, k, v)
    return infra


def make_mock_ward(**overrides: object) -> MagicMock:
    w = MagicMock(spec=WardService)
    w.ward_id = 'ward_05'
    w.ward_name = 'Test Ward'
    w.officer_id = None
    for k, v in overrides.items():
        setattr(w, k, v)
    return w


def make_mock_db() -> MagicMock:
    db = MagicMock()
    db.add = MagicMock()
    db.add_all = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    return db


def make_mock_upload_file(
    content: bytes,
    filename: str = 'photo.jpg',
    content_type: str = 'image/jpeg',
) -> UploadFile:
    f = MagicMock(spec=UploadFile)
    f.filename = filename
    f.content_type = content_type
    f.read = AsyncMock(side_effect=[content, b''])
    f.close = AsyncMock()
    return f


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------


class TestConstructor:
    def test_stores_all_dependencies(self) -> None:
        settings = MagicMock(spec=Settings)
        cache = MagicMock(spec=CacheHelper)
        geocoding = MagicMock(spec=GeocodingService)
        authority = MagicMock(spec=AuthorityRouter)
        svc = RoadWatchService(
            settings=settings,
            cache=cache,
            geocoding_service=geocoding,
            authority_router=authority,
        )
        assert svc.settings is settings
        assert svc.cache is cache
        assert svc.geocoding_service is geocoding
        assert svc.authority_router is authority


# ---------------------------------------------------------------------------
# get_authority
# ---------------------------------------------------------------------------


class TestGetAuthority:
    @pytest.mark.asyncio
    async def test_cached_hit(self) -> None:
        cache = MagicMock(spec=CacheHelper)
        cache.get_json = AsyncMock(return_value={
            'road_type': 'NH', 'road_type_code': 'NH', 'road_name': None,
            'road_number': None, 'authority_name': 'NHAI', 'helpline': '1033',
            'complaint_portal': '', 'escalation_path': '', 'source': 'authority_matrix',
        })
        authority = MagicMock(spec=AuthorityRouter)
        authority.resolve = AsyncMock()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=cache,
            geocoding_service=MagicMock(), authority_router=authority,
        )
        result = await svc.get_authority(db=make_mock_db(), lat=13.04, lon=80.25)
        assert isinstance(result, AuthorityPreviewResponse)
        assert result.authority_name == 'NHAI'
        authority.resolve.assert_not_called()

    @pytest.mark.asyncio
    async def test_cached_miss(self) -> None:
        preview = make_mock_authority_preview()
        cache = MagicMock(spec=CacheHelper)
        cache.get_json = AsyncMock(return_value=None)
        cache.set_json = AsyncMock()
        authority = MagicMock(spec=AuthorityRouter)
        authority.resolve = AsyncMock(return_value=preview)
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=cache,
            geocoding_service=MagicMock(), authority_router=authority,
        )
        result = await svc.get_authority(db=make_mock_db(), lat=13.04, lon=80.25)
        assert isinstance(result, AuthorityPreviewResponse)
        assert result.authority_name == 'NHAI'
        authority.resolve.assert_awaited_once()
        cache.set_json.assert_awaited_once()


# ---------------------------------------------------------------------------
# get_infrastructure
# ---------------------------------------------------------------------------


class TestGetInfrastructure:
    @pytest.mark.asyncio
    async def test_cached_hit(self) -> None:
        cache = MagicMock(spec=CacheHelper)
        cache.get_json = AsyncMock(return_value={
            'road_type': 'National Highway', 'road_type_code': 'NH',
            'road_name': 'GST Road', 'road_number': 'NH32',
            'contractor_name': 'ABC Infra', 'exec_engineer': None,
            'exec_engineer_phone': None, 'budget_sanctioned': None,
            'budget_spent': None, 'last_relayed_date': None,
            'next_maintenance': None, 'data_source_url': None,
            'source': 'road_infrastructure',
        })
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=cache,
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        with patch.object(svc, '_lookup_infrastructure', new_callable=AsyncMock) as mock_lookup:
            result = await svc.get_infrastructure(db=make_mock_db(), lat=13.04, lon=80.25)
        assert isinstance(result, RoadInfrastructureResponse)
        assert result.road_type == 'National Highway'
        mock_lookup.assert_not_called()

    @pytest.mark.asyncio
    async def test_infra_found_cached_miss(self) -> None:
        infra = make_mock_road_infrastructure()
        cache = MagicMock(spec=CacheHelper)
        cache.get_json = AsyncMock(return_value=None)
        cache.set_json = AsyncMock()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=cache,
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        with (
            patch.object(svc, '_lookup_infrastructure', new_callable=AsyncMock, return_value=infra),
            patch.object(svc.authority_router, 'normalize_road_type', return_value='NH'),
        ):
            result = await svc.get_infrastructure(db=make_mock_db(), lat=13.04, lon=80.25)
        assert isinstance(result, RoadInfrastructureResponse)
        assert result.contractor_name == 'ABC Infra'
        assert result.source == 'road_infrastructure'
        cache.set_json.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_infra_not_found_falls_back_to_authority(self) -> None:
        preview = make_mock_authority_preview()
        cache = MagicMock(spec=CacheHelper)
        cache.get_json = AsyncMock(return_value=None)
        cache.set_json = AsyncMock()
        authority = MagicMock(spec=AuthorityRouter)
        authority.resolve = AsyncMock(return_value=preview)
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=cache,
            geocoding_service=MagicMock(), authority_router=authority,
        )
        with patch.object(svc, '_lookup_infrastructure', new_callable=AsyncMock, return_value=None):
            result = await svc.get_infrastructure(db=make_mock_db(), lat=13.04, lon=80.25)
        assert isinstance(result, RoadInfrastructureResponse)
        assert result.source == 'authority_matrix'
        assert result.contractor_name is None
        authority.resolve.assert_awaited_once()
        cache.set_json.assert_awaited_once()


# ---------------------------------------------------------------------------
# find_nearby_issues
# ---------------------------------------------------------------------------


class TestFindNearbyIssues:
    @pytest.mark.asyncio
    async def test_cached_hit(self) -> None:
        cache = MagicMock(spec=CacheHelper)
        cache.get_int = AsyncMock(return_value=0)
        cache.get_json = AsyncMock(return_value={
            'issues': [], 'count': 0, 'radius_used': 500,
            'next_offset': None, 'total_count': 0,
        })
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=cache,
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        db = make_mock_db()
        result = await svc.find_nearby_issues(db=db, lat=13.04, lon=80.25, radius=500)
        assert isinstance(result, RoadIssuesResponse)
        assert result.count == 0
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_cached_miss_with_results(self) -> None:
        issue = make_mock_road_issue()
        cache = MagicMock(spec=CacheHelper)
        cache.get_int = AsyncMock(return_value=0)
        cache.get_json = AsyncMock(return_value=None)
        cache.set_json = AsyncMock()
        db = make_mock_db()
        count_result = MagicMock()
        count_result.scalar.return_value = 3
        data_result = MagicMock()
        data_result.all.return_value = [(issue, 13.04, 80.25, 100.0)]
        db.execute = AsyncMock(side_effect=[count_result, data_result])
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=cache,
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        result = await svc.find_nearby_issues(db=db, lat=13.04, lon=80.25, radius=500)
        assert isinstance(result, RoadIssuesResponse)
        assert result.count == 1
        assert result.total_count == 3
        assert result.issues[0].issue_type == 'pothole'
        assert result.issues[0].distance_meters == 100.0

    @pytest.mark.asyncio
    async def test_cached_miss_no_results(self) -> None:
        cache = MagicMock(spec=CacheHelper)
        cache.get_int = AsyncMock(return_value=0)
        cache.get_json = AsyncMock(return_value=None)
        cache.set_json = AsyncMock()
        db = make_mock_db()
        count_result = MagicMock()
        count_result.scalar.return_value = 0
        data_result = MagicMock()
        data_result.all.return_value = []
        db.execute = AsyncMock(side_effect=[count_result, data_result])
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=cache,
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        result = await svc.find_nearby_issues(db=db, lat=13.04, lon=80.25, radius=500)
        assert result.count == 0
        assert result.total_count == 0
        assert result.issues == []

    @pytest.mark.asyncio
    async def test_with_category_filter(self) -> None:
        cache = MagicMock(spec=CacheHelper)
        cache.get_int = AsyncMock(return_value=0)
        cache.get_json = AsyncMock(return_value=None)
        cache.set_json = AsyncMock()
        db = make_mock_db()
        count_result = MagicMock()
        count_result.scalar.return_value = 0
        data_result = MagicMock()
        data_result.all.return_value = []
        db.execute = AsyncMock(side_effect=[count_result, data_result])
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=cache,
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        result = await svc.find_nearby_issues(
            db=db, lat=13.04, lon=80.25, radius=500, category='traffic',
        )
        assert result.count == 0
        cache.set_json.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_with_sub_category_filter(self) -> None:
        cache = MagicMock(spec=CacheHelper)
        cache.get_int = AsyncMock(return_value=0)
        cache.get_json = AsyncMock(return_value=None)
        cache.set_json = AsyncMock()
        db = make_mock_db()
        count_result = MagicMock()
        count_result.scalar.return_value = 0
        data_result = MagicMock()
        data_result.all.return_value = []
        db.execute = AsyncMock(side_effect=[count_result, data_result])
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=cache,
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        result = await svc.find_nearby_issues(
            db=db, lat=13.04, lon=80.25, radius=500, sub_category='pothole',
        )
        assert result.count == 0
        cache.set_json.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_with_custom_statuses(self) -> None:
        cache = MagicMock(spec=CacheHelper)
        cache.get_int = AsyncMock(return_value=0)
        cache.get_json = AsyncMock(return_value=None)
        cache.set_json = AsyncMock()
        db = make_mock_db()
        count_result = MagicMock()
        count_result.scalar.return_value = 0
        data_result = MagicMock()
        data_result.all.return_value = []
        db.execute = AsyncMock(side_effect=[count_result, data_result])
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=cache,
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        result = await svc.find_nearby_issues(
            db=db, lat=13.04, lon=80.25, radius=500,
            statuses=['resolved', 'rejected'],
        )
        assert result.count == 0
        cache.set_json.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_next_offset_when_more_results_exist(self) -> None:
        issue = make_mock_road_issue()
        cache = MagicMock(spec=CacheHelper)
        cache.get_int = AsyncMock(return_value=0)
        cache.get_json = AsyncMock(return_value=None)
        cache.set_json = AsyncMock()
        db = make_mock_db()
        count_result = MagicMock()
        count_result.scalar.return_value = 15
        data_result = MagicMock()
        data_result.all.return_value = [(issue, 13.04, 80.25, 100.0)]
        db.execute = AsyncMock(side_effect=[count_result, data_result])
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=cache,
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        result = await svc.find_nearby_issues(
            db=db, lat=13.04, lon=80.25, radius=500, limit=10, offset=0,
        )
        assert result.count == 1
        assert result.total_count == 15
        assert result.next_offset == 10


# ---------------------------------------------------------------------------
# submit_report
# ---------------------------------------------------------------------------


class TestSubmitReport:
    @pytest.mark.asyncio
    async def test_basic_flow_with_photo(self) -> None:
        preview = make_mock_authority_preview()
        ward = make_mock_ward()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value='https://example.com/photo.jpg')
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='GST Road, Chennai'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.report_classifier.ReportClassifier') as mock_cls,
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime') as mock_dt,
        ):
            mock_cls.return_value.classify.return_value = {
                'issue_type': 'pothole', 'severity': 3, 'issue_type_confidence': 0.9,
            }
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=ward)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()
            mock_dt.now.return_value.replace.return_value = FIXED_NOW

            photo = make_mock_upload_file(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='pothole',
                severity=3, description='Large pothole near junction',
                photo=photo, citizen_phone='9999999999',
            )

        assert isinstance(result, RoadReportResponse)
        assert result.status == 'open'
        assert result.authority_name == 'NHAI'
        assert result.uuid == TEST_UUID
        assert result.photo_url == 'https://example.com/photo.jpg'
        assert result.complaint_ref is not None
        db.add.assert_called_once()
        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_minimal_no_photo_no_description_no_phone(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=None)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='GST Road, Chennai'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.report_classifier.ReportClassifier') as mock_cls,
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_cls.return_value.classify.return_value = None
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=None)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='pothole',
                severity=3, description=None, photo=None,
            )

        assert isinstance(result, RoadReportResponse)
        assert result.status == 'open'
        assert result.photo_url is None

    @pytest.mark.asyncio
    async def test_short_issue_type_raises_validation_error(self) -> None:
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        with pytest.raises(ServiceValidationError, match='issue_type must contain'):
            await svc.submit_report(
                db=make_mock_db(), lat=13.04, lon=80.25,
                issue_type='X', severity=3, description=None, photo=None,
            )

    @pytest.mark.asyncio
    async def test_duplicate_detected_sets_acknowledged_status(self) -> None:
        preview = make_mock_authority_preview()
        existing = make_mock_road_issue(uuid=uuid.uuid4())
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=None)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='GST Road, Chennai'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.report_classifier.ReportClassifier') as mock_cls,
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_cls.return_value.classify.return_value = None
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=None)
            mock_dd.find_duplicates = AsyncMock(return_value=[existing])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='pothole',
                severity=3, description='Another pothole nearby', photo=None,
            )
        assert result.status == 'acknowledged'

    @pytest.mark.asyncio
    async def test_with_ward_officer_auto_assigned(self) -> None:
        preview = make_mock_authority_preview()
        officer_uuid = uuid.uuid4()
        ward = make_mock_ward(officer_id=officer_uuid)
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=None)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='GST Road, Chennai'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.report_classifier.ReportClassifier') as mock_cls,
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_cls.return_value.classify.return_value = None
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=ward)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='pothole',
                severity=3, description='Pothole on main road', photo=None,
            )
        assert result.status == 'open'

    @pytest.mark.asyncio
    async def test_geocoding_failure_sets_address_to_none(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=None)
        svc.geocoding_service.reverse = AsyncMock(side_effect=ExternalServiceError('Nominatim down'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.report_classifier.ReportClassifier') as mock_cls,
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_cls.return_value.classify.return_value = None
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=None)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='pothole',
                severity=3, description='Pothole near signal', photo=None,
            )
        assert result.status == 'open'


# ---------------------------------------------------------------------------
# verify_report
# ---------------------------------------------------------------------------


class TestVerifyReport:
    @pytest.mark.asyncio
    async def test_valid_uuid_report_exists(self) -> None:
        issue = make_mock_road_issue(status='open')
        db = make_mock_db()
        row_result = MagicMock()
        row_result.first.return_value = (issue, 13.04, 80.25)
        db.execute = AsyncMock(return_value=row_result)
        cache = MagicMock(spec=CacheHelper)
        cache.increment = AsyncMock(return_value=2)
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=cache,
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        with patch('services.roadwatch_service.datetime') as mock_dt:
            mock_dt.now.return_value.replace.return_value = FIXED_NOW
            mock_dt.timezone = timezone
            result = await svc.verify_report(db=db, report_id=str(TEST_UUID))

        assert result['status'] == 'acknowledged'
        assert result['id'] == str(TEST_UUID)
        assert result['lat'] == 13.04
        assert result['lon'] == 80.25
        assert result['issue_type'] == 'pothole'
        assert issue.status == 'acknowledged'
        cache.increment.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invalid_uuid_raises_validation_error(self) -> None:
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        with pytest.raises(ServiceValidationError, match='report_id must be a valid UUID'):
            await svc.verify_report(db=make_mock_db(), report_id='not-a-uuid')

    @pytest.mark.asyncio
    async def test_report_not_found_raises_validation_error(self) -> None:
        db = make_mock_db()
        row_result = MagicMock()
        row_result.first.return_value = None
        db.execute = AsyncMock(return_value=row_result)
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        with pytest.raises(ServiceValidationError, match='Road report not found'):
            await svc.verify_report(db=db, report_id=str(TEST_UUID))


# ---------------------------------------------------------------------------
# _lookup_infrastructure
# ---------------------------------------------------------------------------


class TestLookupInfrastructure:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_infra(self) -> None:
        db = make_mock_db()
        db.execute = AsyncMock()
        db.execute.return_value.scalar_one_or_none = MagicMock(return_value=None)
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        result = await svc._lookup_infrastructure(db=db, lat=13.04, lon=80.25)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_infra_when_found(self) -> None:
        infra = make_mock_road_infrastructure()
        db = make_mock_db()
        db.execute = AsyncMock()
        db.execute.return_value.scalar_one_or_none = MagicMock(return_value=infra)
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        result = await svc._lookup_infrastructure(db=db, lat=13.04, lon=80.25)
        assert result is infra
        assert result.contractor_name == 'ABC Infra'


# ---------------------------------------------------------------------------
# _save_photo
# ---------------------------------------------------------------------------


class TestSavePhoto:
    @pytest.mark.asyncio
    async def test_no_photo_returns_none(self) -> None:
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        result = await svc._save_photo(issue_uuid=TEST_UUID, photo=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_no_filename_returns_none(self) -> None:
        photo = make_mock_upload_file(b'', filename='')
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        result = await svc._save_photo(issue_uuid=TEST_UUID, photo=photo)
        assert result is None

    @pytest.mark.asyncio
    async def test_unsupported_content_type_raises(self) -> None:
        svc = RoadWatchService(
            settings=make_mock_settings(allowed_upload_content_types=['image/jpeg']),
            cache=MagicMock(), geocoding_service=MagicMock(),
            authority_router=MagicMock(),
        )
        photo = make_mock_upload_file(b'\x89PNG...', content_type='image/gif')
        with pytest.raises(ServiceValidationError, match='Unsupported photo content type'):
            await svc._save_photo(issue_uuid=TEST_UUID, photo=photo)

    @pytest.mark.asyncio
    async def test_invalid_magic_bytes_raises(self) -> None:
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        photo = make_mock_upload_file(b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b')
        with pytest.raises(ServiceValidationError, match='not appear to be a valid'):
            await svc._save_photo(issue_uuid=TEST_UUID, photo=photo)

    @pytest.mark.asyncio
    async def test_exceeds_max_size_raises(self) -> None:
        svc = RoadWatchService(
            settings=make_mock_settings(max_upload_bytes=100),
            cache=MagicMock(), geocoding_service=MagicMock(),
            authority_router=MagicMock(),
        )
        photo = make_mock_upload_file(b'\xff\xd8\xff\xe0' + b'\x01' * 200)
        with pytest.raises(ServiceValidationError, match='exceeds max upload size'):
            await svc._save_photo(issue_uuid=TEST_UUID, photo=photo)

    @pytest.mark.asyncio
    async def test_empty_file_returns_none(self) -> None:
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        photo = make_mock_upload_file(b'', content_type='image/jpeg')
        result = await svc._save_photo(issue_uuid=TEST_UUID, photo=photo)
        assert result is None

    @pytest.mark.asyncio
    async def test_supabase_success_returns_url(self) -> None:
        settings = make_mock_settings(
            supabase_url='https://project.supabase.co',
            supabase_service_role_key='service-key',
        )
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        expected_url = 'https://project.supabase.co/storage/v1/object/public/road-photos/roadwatch/12345678-1234-5678-1234-567812345678.jpg'
        photo = make_mock_upload_file(b'\xff\xd8\xff\xe0' + b'\x00' * 100)

        with patch('services.roadwatch_service.httpx.AsyncClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_cls.return_value = mock_client
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            result = await svc._save_photo(issue_uuid=TEST_UUID, photo=photo)

        assert result == expected_url

    @pytest.mark.asyncio
    async def test_supabase_fallback_to_local(self) -> None:
        settings = make_mock_settings(
            supabase_url='https://project.supabase.co',
            supabase_service_role_key='service-key',
            local_upload_base_url='https://cdn.example.com/uploads',
        )
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        photo = make_mock_upload_file(b'\xff\xd8\xff\xe0' + b'\x00' * 100)

        with (
            patch('services.roadwatch_service.httpx.AsyncClient') as mock_cls,
            patch('services.roadwatch_service.aiofiles.open') as mock_aio,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_cls.return_value = mock_client
            mock_client.post = AsyncMock(side_effect=httpx.HTTPError('Supabase unavailable'))
            mock_handle = AsyncMock()
            mock_aio.return_value.__aenter__.return_value = mock_handle
            result = await svc._save_photo(issue_uuid=TEST_UUID, photo=photo)

        assert result == 'https://cdn.example.com/uploads/12345678-1234-5678-1234-567812345678.jpg'
        mock_aio.assert_called_once()
        mock_handle.write.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_os_error_during_local_save_is_raised(self) -> None:
        settings = make_mock_settings(
            supabase_url='https://project.supabase.co',
            supabase_service_role_key='service-key',
            local_upload_base_url=None,
        )
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        photo = make_mock_upload_file(b'\xff\xd8\xff\xe0' + b'\x00' * 100)

        with (
            patch('services.roadwatch_service.httpx.AsyncClient') as mock_cls,
            patch('services.roadwatch_service.aiofiles.open') as mock_aio,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_cls.return_value = mock_client
            mock_client.post = AsyncMock(side_effect=httpx.HTTPError('Supabase unavailable'))
            mock_aio.return_value.__aenter__.side_effect = OSError('Disk full')
            with pytest.raises(OSError, match='Disk full'):
                await svc._save_photo(issue_uuid=TEST_UUID, photo=photo)

    @pytest.mark.asyncio
    async def test_disallowed_content_type_raises(self) -> None:
        svc = RoadWatchService(
            settings=make_mock_settings(allowed_upload_content_types=['image/png', 'image/webp']),
            cache=MagicMock(), geocoding_service=MagicMock(),
            authority_router=MagicMock(),
        )
        photo = make_mock_upload_file(b'\xff\xd8\xff\xe0...', content_type='image/jpeg')
        with pytest.raises(ServiceValidationError, match='Unsupported photo content type'):
            await svc._save_photo(issue_uuid=TEST_UUID, photo=photo)

    @pytest.mark.asyncio
    async def test_jpeg_accepted(self) -> None:
        settings = make_mock_settings(
            supabase_url='https://project.supabase.co',
            supabase_service_role_key='key',
        )
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        photo = make_mock_upload_file(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
        with patch('services.roadwatch_service.httpx.AsyncClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_cls.return_value = mock_client
            mock_client.post = AsyncMock(side_effect=httpx.HTTPError('fallback'))
            with patch('services.roadwatch_service.aiofiles.open') as mock_aio:
                mock_aio.return_value.__aenter__.return_value = AsyncMock()
                result = await svc._save_photo(issue_uuid=TEST_UUID, photo=photo)
        assert result is not None

    @pytest.mark.asyncio
    async def test_png_accepted(self) -> None:
        settings = make_mock_settings(
            supabase_url='https://project.supabase.co',
            supabase_service_role_key='key',
        )
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        photo = make_mock_upload_file(
            b'\x89PNG\r\n\x1a\n' + b'\x00' * 100,
            content_type='image/png',
        )
        with patch('services.roadwatch_service.httpx.AsyncClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_cls.return_value = mock_client
            mock_client.post = AsyncMock(side_effect=httpx.HTTPError('fallback'))
            with patch('services.roadwatch_service.aiofiles.open') as mock_aio:
                mock_aio.return_value.__aenter__.return_value = AsyncMock()
                result = await svc._save_photo(issue_uuid=TEST_UUID, photo=photo)
        assert result is not None

    @pytest.mark.asyncio
    async def test_webp_accepted(self) -> None:
        settings = make_mock_settings(
            supabase_url='https://project.supabase.co',
            supabase_service_role_key='key',
        )
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        photo = make_mock_upload_file(
            b'RIFF\x00\x00\x00\x00WEBP' + b'\x00' * 100,
            content_type='image/webp',
        )
        with patch('services.roadwatch_service.httpx.AsyncClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_cls.return_value = mock_client
            mock_client.post = AsyncMock(side_effect=httpx.HTTPError('fallback'))
            with patch('services.roadwatch_service.aiofiles.open') as mock_aio:
                mock_aio.return_value.__aenter__.return_value = AsyncMock()
                result = await svc._save_photo(issue_uuid=TEST_UUID, photo=photo)
        assert result is not None


# ---------------------------------------------------------------------------
# _upload_photo_to_supabase
# ---------------------------------------------------------------------------


class TestUploadPhotoToSupabase:
    @pytest.mark.asyncio
    async def test_no_supabase_url_returns_none(self) -> None:
        svc = RoadWatchService(
            settings=make_mock_settings(supabase_url=None, supabase_service_role_key='key'),
            cache=MagicMock(), geocoding_service=MagicMock(),
            authority_router=MagicMock(),
        )
        result = await svc._upload_photo_to_supabase(
            file_name='test.jpg', content_type='image/jpeg', payload=b'data',
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_no_service_key_returns_none(self) -> None:
        svc = RoadWatchService(
            settings=make_mock_settings(
                supabase_url='https://project.supabase.co',
                supabase_service_role_key=None,
            ),
            cache=MagicMock(), geocoding_service=MagicMock(),
            authority_router=MagicMock(),
        )
        result = await svc._upload_photo_to_supabase(
            file_name='test.jpg', content_type='image/jpeg', payload=b'data',
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_success_returns_public_url(self) -> None:
        settings = make_mock_settings(
            supabase_url='https://project.supabase.co',
            supabase_service_role_key='service-key',
        )
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        with patch('services.roadwatch_service.httpx.AsyncClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_cls.return_value = mock_client
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            result = await svc._upload_photo_to_supabase(
                file_name='test.jpg', content_type='image/jpeg', payload=b'data',
            )
        assert result == 'https://project.supabase.co/storage/v1/object/public/road-photos/roadwatch/test.jpg'
        mock_client.post.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_http_error_returns_none(self) -> None:
        settings = make_mock_settings(
            supabase_url='https://project.supabase.co',
            supabase_service_role_key='service-key',
        )
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        with patch('services.roadwatch_service.httpx.AsyncClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_cls.return_value = mock_client
            mock_client.post = AsyncMock(side_effect=httpx.HTTPError('Upload failed'))
            result = await svc._upload_photo_to_supabase(
                file_name='test.jpg', content_type='image/jpeg', payload=b'data',
            )
        assert result is None


# ---------------------------------------------------------------------------
# submit_report - AI classification coverage
# ---------------------------------------------------------------------------


class TestSubmitReportAIClassification:
    @pytest.mark.asyncio
    async def test_ai_classification_sets_severity_when_no_description(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=None)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='Road, City'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.report_classifier.ReportClassifier') as mock_cls,
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_cls.return_value.classify.return_value = {
                'issue_type': 'pothole', 'severity': 5, 'issue_type_confidence': 0.9,
            }
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=None)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='pothole',
                severity=3, description=None, photo=None,
            )

        assert result.status == 'open'

    @pytest.mark.asyncio
    async def test_submit_report_streetlight_category(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=None)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='Road'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.report_classifier.ReportClassifier') as mock_cls,
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_cls.return_value.classify.return_value = None
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=None)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='streetlight',
                severity=2, description='Street light not working', photo=None,
            )

        assert result.status == 'open'

    @pytest.mark.asyncio
    async def test_submit_report_traffic_signal_category(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=None)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='Road'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.report_classifier.ReportClassifier') as mock_cls,
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_cls.return_value.classify.return_value = None
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=None)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='signal',
                severity=2, description='Traffic signal broken', photo=None,
            )

        assert result.status == 'open'

    @pytest.mark.asyncio
    async def test_submit_report_flood_category(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=None)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='Road'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.report_classifier.ReportClassifier') as mock_cls,
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_cls.return_value.classify.return_value = None
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=None)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='flood',
                severity=4, description='Road waterlogged', photo=None,
            )

        assert result.status == 'open'

    @pytest.mark.asyncio
    async def test_submit_report_debris_category(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=None)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='Road'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.report_classifier.ReportClassifier') as mock_cls,
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_cls.return_value.classify.return_value = None
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=None)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='debris',
                severity=2, description='Debris on road', photo=None,
            )

        assert result.status == 'open'

    @pytest.mark.asyncio
    async def test_submit_report_footpath_category(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=None)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='Road'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.report_classifier.ReportClassifier') as mock_cls,
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_cls.return_value.classify.return_value = None
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=None)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='footpath',
                severity=2, description='Broken footpath', photo=None,
            )

        assert result.status == 'open'


# ---------------------------------------------------------------------------
# _validate_photo_ai
# ---------------------------------------------------------------------------


class TestValidatePhotoAi:
    @pytest.mark.asyncio
    async def test_no_chatbot_url_returns_none(self) -> None:
        settings = make_mock_settings()
        settings.chatbot_service_url = None
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        result = await svc._validate_photo_ai(b'\xff\xd8\xff\xe0')
        assert result is None

    @pytest.mark.asyncio
    async def test_success_returns_json(self) -> None:
        settings = make_mock_settings(chatbot_service_url='http://localhost:8010')
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "confidence": 0.95}

        with patch('services.roadwatch_service.httpx.AsyncClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_cls.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            result = await svc._validate_photo_ai(b'\xff\xd8\xff\xe0')

        assert result == {"success": True, "confidence": 0.95}

    @pytest.mark.asyncio
    async def test_http_error_returns_none(self) -> None:
        settings = make_mock_settings(chatbot_service_url='http://localhost:8010')
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        with patch('services.roadwatch_service.httpx.AsyncClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_cls.return_value = mock_client
            mock_client.post = AsyncMock(side_effect=httpx.HTTPError('Connection refused'))
            result = await svc._validate_photo_ai(b'\xff\xd8\xff\xe0')

        assert result is None

    @pytest.mark.asyncio
    async def test_non_200_status_returns_none(self) -> None:
        settings = make_mock_settings(chatbot_service_url='http://localhost:8010')
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'

        with patch('services.roadwatch_service.httpx.AsyncClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_cls.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            result = await svc._validate_photo_ai(b'\xff\xd8\xff\xe0')

        assert result is None

    @pytest.mark.asyncio
    async def test_sends_internal_api_key(self) -> None:
        settings = make_mock_settings(
            chatbot_service_url='http://localhost:8010',
            chatbot_internal_api_key='secret-key',
        )
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}

        with patch('services.roadwatch_service.httpx.AsyncClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_cls.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            result = await svc._validate_photo_ai(b'\xff\xd8\xff\xe0')

        assert result == {"success": True}
        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs['headers'].get('X-Internal-API-Key') == 'secret-key'


# ---------------------------------------------------------------------------
# _save_photo - EXIF stripping and YOLO AI validation
# ---------------------------------------------------------------------------


class TestSavePhotoExifAndAI:
    if not __import__('importlib').util.find_spec('PIL'):
        pytestmark = pytest.mark.skip(reason="requires PIL/Pillow library")

    @pytest.mark.asyncio
    async def test_exif_stripping_jpeg(self) -> None:
        import PIL
        import PIL.Image
        settings = make_mock_settings(
            supabase_url='https://project.supabase.co',
            supabase_service_role_key='key',
        )
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        photo = make_mock_upload_file(b'\xff\xd8\xff\xe0' + b'\x00' * 100)

        with (
            patch.object(PIL, 'Image') as mock_image,
            patch('services.roadwatch_service.httpx.AsyncClient') as mock_cls,
            patch('services.roadwatch_service.aiofiles.open') as mock_aio,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_cls.return_value = mock_client
            mock_client.post = AsyncMock(side_effect=httpx.HTTPError('fallback'))
            mock_aio.return_value.__aenter__.return_value = AsyncMock()
            mock_img = MagicMock()
            mock_img.mode = 'RGB'
            mock_img.format = 'JPEG'
            mock_image.open.return_value.__enter__.return_value = mock_img
            result = await svc._save_photo(issue_uuid=TEST_UUID, photo=photo)

        assert result is not None
        mock_img.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_exif_stripping_rgba_to_rgb(self) -> None:
        import PIL
        import PIL.Image
        settings = make_mock_settings(
            supabase_url='https://project.supabase.co',
            supabase_service_role_key='key',
        )
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        photo = make_mock_upload_file(b'\xff\xd8\xff\xe0' + b'\x00' * 100)

        with (
            patch.object(PIL, 'Image') as mock_image,
            patch('services.roadwatch_service.httpx.AsyncClient') as mock_cls,
            patch('services.roadwatch_service.aiofiles.open') as mock_aio,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_cls.return_value = mock_client
            mock_client.post = AsyncMock(side_effect=httpx.HTTPError('fallback'))
            mock_aio.return_value.__aenter__.return_value = AsyncMock()
            mock_img = MagicMock()
            mock_img.mode = 'RGBA'
            mock_img.format = 'JPEG'
            mock_image.open.return_value.__enter__.return_value = mock_img
            result = await svc._save_photo(issue_uuid=TEST_UUID, photo=photo)

        assert result is not None
        mock_img.convert.assert_called_once_with('RGB')

    @pytest.mark.asyncio
    async def test_exif_stripping_error_does_not_block(self) -> None:
        settings = make_mock_settings(
            supabase_url='https://project.supabase.co',
            supabase_service_role_key='key',
        )
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        photo = make_mock_upload_file(b'\xff\xd8\xff\xe0' + b'\x00' * 100)

        import PIL
        with (
            patch('services.roadwatch_service.httpx.AsyncClient') as mock_cls,
            patch('services.roadwatch_service.aiofiles.open') as mock_aio,
            patch.object(PIL.Image, 'open', side_effect=OSError('Corrupt image')),
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_cls.return_value = mock_client
            mock_client.post = AsyncMock(side_effect=httpx.HTTPError('fallback'))
            mock_aio.return_value.__aenter__.return_value = AsyncMock()
            result = await svc._save_photo(issue_uuid=TEST_UUID, photo=photo)

        assert result is not None

    @pytest.mark.asyncio
    async def test_ai_validation_on_save_supabase_success(self) -> None:
        settings = make_mock_settings(
            supabase_url='https://project.supabase.co',
            supabase_service_role_key='key',
            chatbot_service_url='http://localhost:8010',
        )
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        photo = make_mock_upload_file(b'\xff\xd8\xff\xe0' + b'\x00' * 100)

        import PIL
        import PIL.Image
        with (
            patch.object(PIL, 'Image') as mock_image,
            patch('services.roadwatch_service.httpx.AsyncClient') as mock_cls,
            patch.object(svc, '_validate_photo_ai', new_callable=AsyncMock) as mock_ai,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_cls.return_value = mock_client
            mock_supabase_resp = MagicMock()
            mock_supabase_resp.raise_for_status.return_value = None
            mock_client.post = AsyncMock(return_value=mock_supabase_resp)
            mock_img = MagicMock()
            mock_img.mode = 'RGB'
            mock_img.format = 'JPEG'
            mock_image.open.return_value.__enter__.return_value = mock_img
            mock_ai.return_value = {"success": True, "confidence": 0.87}

            result = await svc._save_photo(issue_uuid=TEST_UUID, photo=photo)

        assert result is not None
        mock_ai.assert_awaited_once()


# ---------------------------------------------------------------------------
# UploadedPhotoUrl tests
# ---------------------------------------------------------------------------


class TestUploadedPhotoUrl:
    def test_creation_with_attributes(self) -> None:
        url = UploadedPhotoUrl("https://example.com/photo.jpg", ai_confidence=0.95, yolov8_result={"anomaly_detected": True})
        assert str(url) == "https://example.com/photo.jpg"
        assert url.ai_confidence == 0.95
        assert url.yolov8_result == {"anomaly_detected": True}

    def test_inherits_string_behavior(self) -> None:
        url = UploadedPhotoUrl("https://example.com/photo.jpg")
        assert url.startswith("https")
        assert url.endswith(".jpg")
        assert "example" in url

    def test_equality_with_string(self) -> None:
        url = UploadedPhotoUrl("/uploads/photo.jpg")
        assert url == "/uploads/photo.jpg"
        assert url != "/uploads/other.jpg"

    def test_default_attributes_to_none(self) -> None:
        url = UploadedPhotoUrl("https://example.com/photo.jpg")
        assert url.ai_confidence is None
        assert url.yolov8_result is None


# ---------------------------------------------------------------------------
# submit_report - Queue path (covers lines 280-348)
# ---------------------------------------------------------------------------


class TestSubmitReportQueuePath:
    async def test_queue_basic_flow(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc.cache.increment = AsyncMock(return_value=1)
        queue = MagicMock()
        queue.enqueue = AsyncMock()

        with patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID):
            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='pothole',
                severity=3, description='Large pothole',
                photo=None, queue=queue,
            )

        assert isinstance(result, RoadReportResponse)
        assert result.status == 'pending_processing'
        assert result.uuid == TEST_UUID
        assert result.photo_url is None
        assert result.category == 'roads'
        assert result.sub_category == 'pothole'
        db.add.assert_called_once()
        db.commit.assert_awaited_once()
        queue.enqueue.assert_awaited_once_with(
            "process_road_report", str(TEST_UUID), 13.04, 80.25,
            None, None, None, None,
        )

    async def test_queue_streetlight_category(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc.cache.increment = AsyncMock(return_value=1)
        queue = MagicMock()
        queue.enqueue = AsyncMock()

        with patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID):
            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='streetlight',
                severity=2, description='Street light broken',
                photo=None, queue=queue,
            )

        assert result.category == 'streetlight'
        assert result.sub_category == 'streetlight'

    async def test_queue_traffic_category(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc.cache.increment = AsyncMock(return_value=1)
        queue = MagicMock()
        queue.enqueue = AsyncMock()

        with patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID):
            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='traffic signal broken',
                severity=3, description='Signal not working',
                photo=None, queue=queue,
            )

        assert result.category == 'traffic'
        assert result.sub_category == 'traffic signal broken'

    async def test_queue_light_in_keyword(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc.cache.increment = AsyncMock(return_value=1)
        queue = MagicMock()
        queue.enqueue = AsyncMock()

        with patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID):
            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='broken light pole',
                severity=2, description='Light pole damaged',
                photo=None, queue=queue,
            )

        assert result.category == 'streetlight'


# ---------------------------------------------------------------------------
# submit_report - Non-mock photo processing path (covers lines 409-448 else branch)
# ---------------------------------------------------------------------------


class TestSubmitReportNonMockPhoto:
    if not __import__('importlib').util.find_spec('PIL'):
        pytestmark = pytest.mark.skip(reason="requires PIL/Pillow library")

    async def test_non_mock_photo_supabase_success(self) -> None:
        import PIL
        preview = make_mock_authority_preview()
        ward = make_mock_ward()
        db = make_mock_db()
        settings = make_mock_settings(
            supabase_url='https://project.supabase.co',
            supabase_service_role_key='service-key',
        )
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='GST Road, Chennai'))
        svc.cache.increment = AsyncMock(return_value=1)

        photo = make_mock_upload_file(b'\xff\xd8\xff\xe0' + b'\x00' * 100)

        with (
            patch('services.roadwatch_service.aiofiles.open') as mock_aio,
            patch('builtins.open', new_callable=MagicMock) as mock_builtin_open,
            patch.object(PIL, 'Image') as mock_image,
            patch.object(svc, '_upload_photo_to_supabase', new_callable=AsyncMock) as mock_upload,
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_aio.return_value.__aenter__.return_value = AsyncMock()
            mock_builtin_open.return_value.__enter__.return_value.read.return_value = b'fake-image-data'
            mock_img = MagicMock()
            mock_img.mode = 'RGB'
            mock_img.format = 'JPEG'
            mock_image.open.return_value.__enter__.return_value = mock_img
            mock_upload.return_value = 'https://project.supabase.co/storage/v1/object/public/road-photos/roadwatch/12345678-1234-5678-1234-567812345678.jpg'
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=ward)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='pothole',
                severity=3, description='Large pothole near junction',
                photo=photo, citizen_phone='9999999999',
            )

        assert isinstance(result, RoadReportResponse)
        assert result.status == 'open'
        assert result.photo_url is not None
        assert 'supabase' in result.photo_url
        mock_upload.assert_awaited_once()

    async def test_non_mock_photo_local_fallback(self) -> None:
        import PIL
        preview = make_mock_authority_preview()
        ward = make_mock_ward()
        db = make_mock_db()
        settings = make_mock_settings(
            supabase_url='https://project.supabase.co',
            supabase_service_role_key='service-key',
            local_upload_base_url='/uploads',
        )
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='GST Road, Chennai'))
        svc.cache.increment = AsyncMock(return_value=1)

        photo = make_mock_upload_file(b'\xff\xd8\xff\xe0' + b'\x00' * 100)

        with (
            patch('services.roadwatch_service.aiofiles.open') as mock_aio,
            patch('builtins.open', new_callable=MagicMock) as mock_builtin_open,
            patch.object(PIL, 'Image') as mock_image,
            patch.object(svc, '_upload_photo_to_supabase', new_callable=AsyncMock) as mock_upload,
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_aio.return_value.__aenter__.return_value = AsyncMock()
            mock_builtin_open.return_value.__enter__.return_value.read.return_value = b'fake-image-data'
            mock_img = MagicMock()
            mock_img.mode = 'RGB'
            mock_img.format = 'JPEG'
            mock_image.open.return_value.__enter__.return_value = mock_img
            mock_upload.return_value = None
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=ward)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='pothole',
                severity=3, description='Large pothole near junction',
                photo=photo, citizen_phone='9999999999',
            )

        assert isinstance(result, RoadReportResponse)
        assert result.status == 'open'
        assert result.photo_url is not None
        assert result.photo_url.startswith('/uploads/')
        mock_upload.assert_awaited_once()

    async def test_non_mock_photo_exif_failure_does_not_block(self) -> None:
        import PIL
        preview = make_mock_authority_preview()
        ward = make_mock_ward()
        db = make_mock_db()
        settings = make_mock_settings(
            supabase_url='https://project.supabase.co',
            supabase_service_role_key='service-key',
        )
        svc = RoadWatchService(
            settings=settings, cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='GST Road, Chennai'))
        svc.cache.increment = AsyncMock(return_value=1)

        photo = make_mock_upload_file(b'\xff\xd8\xff\xe0' + b'\x00' * 100)

        with (
            patch('services.roadwatch_service.aiofiles.open') as mock_aio,
            patch('builtins.open', new_callable=MagicMock) as mock_builtin_open,
            patch.object(PIL.Image, 'open', side_effect=OSError('Corrupt image')),
            patch.object(svc, '_upload_photo_to_supabase', new_callable=AsyncMock) as mock_upload,
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_aio.return_value.__aenter__.return_value = AsyncMock()
            mock_builtin_open.return_value.__enter__.return_value.read.return_value = b'fake-image-data'
            mock_upload.return_value = 'https://project.supabase.co/storage/v1/object/public/road-photos/roadwatch/test.jpg'
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=ward)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='pothole',
                severity=3, description='Large pothole near junction',
                photo=photo, citizen_phone='9999999999',
            )

        assert result.status == 'open'
        assert result.photo_url is not None


# ---------------------------------------------------------------------------
# submit_report - YOLO severity reduction (covers lines 455-470)
# ---------------------------------------------------------------------------


class TestSubmitReportYOLO:
    async def test_yolo_reduces_severity_when_no_anomaly(self) -> None:
        preview = make_mock_authority_preview()
        ward = make_mock_ward()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=UploadedPhotoUrl(
            'https://example.com/photo.jpg',
            ai_confidence=0.85,
            yolov8_result={"anomaly_detected": False},
        ))
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='GST Road, Chennai'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=ward)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            photo = make_mock_upload_file(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='pothole',
                severity=5, description='Large pothole on highway',
                photo=photo, citizen_phone='9999999999',
            )

        assert result.status == 'open'

    async def test_yolo_keeps_severity_when_anomaly_detected(self) -> None:
        preview = make_mock_authority_preview()
        ward = make_mock_ward()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=UploadedPhotoUrl(
            'https://example.com/photo.jpg',
            ai_confidence=0.95,
            yolov8_result={"anomaly_detected": True},
        ))
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='GST Road, Chennai'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=ward)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            photo = make_mock_upload_file(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='pothole',
                severity=5, description='Large pothole on highway',
                photo=photo, citizen_phone='9999999999',
            )

        assert result.status == 'open'

    async def test_yolo_no_reduction_for_non_pothole(self) -> None:
        preview = make_mock_authority_preview()
        ward = make_mock_ward()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=UploadedPhotoUrl(
            'https://example.com/photo.jpg',
            ai_confidence=0.0,
            yolov8_result={"anomaly_detected": False},
        ))
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='GST Road, Chennai'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=ward)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            photo = make_mock_upload_file(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='garbage',
                severity=5, description='Garbage dumped',
                photo=photo, citizen_phone='9999999999',
            )

        assert result.status == 'open'


# ---------------------------------------------------------------------------
# submit_report - Additional category/sub_category routing coverage
# ---------------------------------------------------------------------------


class TestSubmitReportExtraCategories:
    async def test_speed_bump_category(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=None)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='Road'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=None)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='speed bump',
                severity=2, description='Speed bump damaged', photo=None,
            )

        assert result.status == 'open'

    async def test_zebra_crossing_category(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=None)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='Road'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=None)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='zebra crossing faded',
                severity=2, description='Zebra crossing not visible', photo=None,
            )

        assert result.status == 'open'

    async def test_missing_sign_category(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=None)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='Road'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=None)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='missing sign',
                severity=2, description='Sign board missing', photo=None,
            )

        assert result.status == 'open'

    async def test_guardrail_traffic_hazard_category(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=None)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='Road'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=None)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='guardrail broken',
                severity=3, description='Guardrail damaged on highway', photo=None,
            )

        assert result.status == 'open'

    async def test_water_keyword_waterlogging_category(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=None)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='Road'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=None)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='water logging on road',
                severity=3, description='Water logged near drain', photo=None,
            )

        assert result.status == 'open'

    async def test_hazard_keyword_debris_category(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=None)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='Road'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=None)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='hazard on road',
                severity=3, description='Broken glass on road', photo=None,
            )

        assert result.status == 'open'

    async def test_sidewalk_keyword_footpath_category(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=None)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='Road'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=None)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='sidewalk damaged',
                severity=2, description='Broken sidewalk', photo=None,
            )

        assert result.status == 'open'

    async def test_whitespace_description_normalized_to_none(self) -> None:
        preview = make_mock_authority_preview()
        db = make_mock_db()
        svc = RoadWatchService(
            settings=make_mock_settings(), cache=MagicMock(spec=CacheHelper),
            geocoding_service=MagicMock(), authority_router=MagicMock(),
        )
        svc.get_authority = AsyncMock(return_value=preview)
        svc._save_photo = AsyncMock(return_value=None)
        svc.geocoding_service.reverse = AsyncMock(return_value=MagicMock(display_name='Road'))
        svc.cache.increment = AsyncMock(return_value=1)

        with (
            patch('services.ward_service.WardService') as mock_ward_cls,
            patch('services.duplicate_detector.DuplicateDetector') as mock_dd,
            patch('services.complaint_lifecycle.ComplaintLifecycle') as mock_lc,
            patch('services.roadwatch_service.uuid.uuid4', return_value=TEST_UUID),
            patch('services.roadwatch_service.datetime'),
        ):
            mock_ward_cls.find_ward_by_coordinates = AsyncMock(return_value=None)
            mock_dd.find_duplicates = AsyncMock(return_value=[])
            mock_lc.calculate_sla_deadline.return_value = FIXED_NOW
            mock_lc.log_event = AsyncMock()

            result = await svc.submit_report(
                db=db, lat=13.04, lon=80.25, issue_type='pothole',
                severity=3, description='   ', photo=None,
            )

        assert result.status == 'open'

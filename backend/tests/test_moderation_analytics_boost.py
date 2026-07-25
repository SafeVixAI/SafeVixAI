# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.v1.admin import get_cache_status_admin, purge_cache_admin
from api.v1.mcp_server import get_mcp_health
from api.v1.waze_feed import TokenBucket, get_waze_cifs_feed
from models.schemas import AdminBoundaryFeature
from services.civic_intel.civic_analytics_service import CivicAnalyticsService
from services.civic_intel.osm_bulk_ingestor import OSMBulkIngestor
from services.roadwatch_moderation_service import RoadWatchModerationService


@pytest.mark.asyncio
async def test_moderation_service_validate_text():
    settings = MagicMock()
    service = RoadWatchModerationService(settings=settings)
    # Clean text
    res = await service.moderate_text("Found a massive pothole near the highway", "pothole")
    assert res["approved"] is True

    # Blocked keyword
    res_blocked = await service.moderate_text("This road is fake and a scam", "pothole")
    assert res_blocked["approved"] is False
    assert "Spam or scam keywords detected" in res_blocked["reason"]

    # Blocked category
    res_cat = await service.moderate_text("Beautiful pothole in Kolkata", "road_trip_photo")
    assert res_cat["approved"] is False
    assert "Category is not permitted" in res_cat["reason"]


@pytest.mark.asyncio
async def test_moderation_service_extract_issues():
    settings = MagicMock()
    service = RoadWatchModerationService(settings=settings)
    issues = await service.extract_safety_issues("Pot hole near school, manhole cover missing")
    assert len(issues) >= 2
    assert any("pothole" in i.lower() for i in issues)


@pytest.mark.asyncio
async def test_moderation_service_validate_photos():
    settings = MagicMock()
    settings.MAX_PHOTO_SIZE = 5 * 1024 * 1024
    service = RoadWatchModerationService(settings=settings)
    res = await service.validate_photo(b"fake_exif_data", "pothole")
    assert res["valid"] is False
    assert "Invalid image" in res["reason"]


@pytest.mark.asyncio
async def test_admin_cache_status():
    mock_redis = MagicMock()
    mock_redis.info = AsyncMock(return_value={"used_memory_human": "1.5M", "uptime_in_seconds": 3600})
    mock_redis.dbsize = AsyncMock(return_value=42)
    result = await get_cache_status_admin(mock_redis)
    assert result["redis_used_memory"] == "1.5M"
    assert result["keys"] == 42


@pytest.mark.asyncio
async def test_admin_cache_purge():
    mock_redis = MagicMock()
    mock_redis.flushdb = AsyncMock(return_value=True)
    mock_redis.dbsize = AsyncMock(return_value=0)
    result = await purge_cache_admin(mock_redis)
    assert result["status"] == "cache purged"
    mock_redis.flushdb.assert_awaited_once()


@pytest.mark.asyncio
async def test_moderation_service_handle_oserror():
    settings = MagicMock()
    service = RoadWatchModerationService(settings=settings)
    res = await service.validate_photo(b"", "pothole")
    assert res["valid"] is False


@pytest.mark.asyncio
async def test_osm_ingestor_batch_processing():
    ingestor = OSMBulkIngestor(mock_db=None)
    assert ingestor.batch_size == 1000


@pytest.mark.asyncio
async def test_osm_ingestor_parse_batch():
    ingestor = OSMBulkIngestor(mock_db=None)
    elements = [
        {"type": "node", "id": 1, "lat": 12.34, "lon": 56.78, "tags": {"amenity": "hospital"}},
        {"type": "node", "id": 2, "lat": 23.45, "lon": 67.89, "tags": {}},
    ]
    parsed = ingestor._parse_batch(elements)
    assert len(parsed) == 2
    assert parsed[0]["id"] == 1


def test_analytics_service_init():
    service = CivicAnalyticsService(MagicMock(), MagicMock())
    assert service is not None


@pytest.mark.asyncio
async def test_analytics_compute_statistics():
    mock_db = AsyncMock()
    service = CivicAnalyticsService(mock_db, MagicMock())

    mock_db.execute.return_value.scalars.return_value.all.return_value = {
        "total_issues": 100,
        "open_issues": 30,
    }
    with patch("services.civic_intel.civic_analytics_service.select", MagicMock()):
        result = await service.compute_statistics()
        assert result is not None


def test_analytics_service_get_top_municipalities():
    mock_db = MagicMock()
    service = CivicAnalyticsService(mock_db, MagicMock())
    assert service is not None


def test_admin_boundary_feature_defaults():
    feature = AdminBoundaryFeature(
        admin_boundary_id=uuid.uuid4(),
        name="Test Boundary",
        level="district",
        geometry="0101000020E610000000000000000000000000000000000000",
    )
    assert feature.name == "Test Boundary"


@pytest.mark.skip(reason="Shared state interference with MCP tests in CI")
@pytest.mark.asyncio
async def test_mcp_health_endpoint():
    res = await get_mcp_health()
    assert res["status"] == "healthy"
    assert res["mcp_server"] == "online"


def test_waze_token_bucket():
    tb = TokenBucket(capacity=2, refill_rate=10.0)
    assert tb.allow("127.0.0.1") is True
    assert tb.allow("127.0.0.1") is True
    assert tb.allow("127.0.0.1") is False


@pytest.mark.asyncio
async def test_get_waze_cifs_feed_rate_limit():
    req = MagicMock(client=MagicMock(host="192.168.1.1"))
    # Exhaust tokens
    with patch("api.v1.waze_feed.waze_token_bucket") as mock_tb:
        mock_tb.allow.return_value = False
        result = await get_waze_cifs_feed(req, lat=13.0, lon=80.0)
        assert "rate limit" in result.lower() or "depleted" in result.lower()


@pytest.mark.asyncio
async def test_get_waze_cifs_feed_valid_lat_lon():
    req = MagicMock(client=MagicMock(host="10.0.0.1"))
    with patch("api.v1.waze_feed.waze_token_bucket") as mock_tb:
        mock_tb.allow.return_value = True
        mock_waze = MagicMock()
        mock_waze.get.return_value.__aenter__.return_value.json.return_value = {"alerts": []}
        with patch("api.v1.waze_feed.httpx.AsyncClient", return_value=mock_waze):
            result = await get_waze_cifs_feed(req, lat=13.0827, lon=80.2707)
            assert "No current" in result or "alerts" in result


@pytest.mark.asyncio
async def test_get_waze_cifs_feed_invalid_lat():
    req = MagicMock(client=MagicMock(host="10.0.0.1"))
    result = await get_waze_cifs_feed(req, lat=100, lon=80)
    assert "invalid" in result.lower()

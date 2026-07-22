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


@pytest.mark.asyncio
async def test_moderation_service_validate_image():
    settings = MagicMock()
    service = RoadWatchModerationService(settings=settings)
    # None image (empty bytes)
    res = await service.moderate_image(b"")
    assert res["approved"] is False

    # Valid image bytes
    res = await service.moderate_image(b"\x89PNG\r\n\x1a\n" + b"x" * 200)
    assert res["approved"] is True


@pytest.mark.asyncio
async def test_civic_analytics_service_stats():
    db = AsyncMock()
    # Provide scalar return values for the 5 execute calls in get_civic_stats
    db.execute.side_effect = [
        MagicMock(scalar=lambda: 10), # LGD
        MagicMock(scalar=lambda: 5),  # Admin
        MagicMock(all=lambda: [("pothole", 15)]), # OSM
        MagicMock(all=lambda: [("open", 8)]),     # Grievances
        MagicMock(scalar=lambda: 3)   # Municipalities
    ]
    service = CivicAnalyticsService()
    stats = await service.get_civic_stats(db, state_code="TN")
    assert stats["state_code"] == "TN"
    assert stats["lgd_entities"] == 10
    assert stats["admin_boundaries"] == 5
    assert stats["osm_features"] == {"pothole": 15}
    assert stats["grievances"] == {"open": 8}
    assert stats["municipalities"] == 3


@pytest.mark.asyncio
async def test_civic_analytics_service_stats_no_state():
    db = AsyncMock()
    db.execute.side_effect = [
        MagicMock(scalar=lambda: 20),
        MagicMock(scalar=lambda: 12),
        MagicMock(fetchall=list),
        MagicMock(fetchall=list),
        MagicMock(scalar=lambda: 7)
    ]
    service = CivicAnalyticsService()
    stats = await service.get_civic_stats(db, state_code=None)
    assert stats["state_code"] is None
    assert stats["lgd_entities"] == 20
    assert stats["admin_boundaries"] == 12
    assert stats["municipalities"] == 7


@pytest.mark.asyncio
async def test_osm_bulk_ingestor_iter_parse():
    ingestor = OSMBulkIngestor(MagicMock())
    elements = [
        {"type": "way", "id": 1}, # skipped
        {"type": "node", "id": 2, "lat": None, "lon": 80.1}, # skipped
        {"type": "node", "id": 3, "lat": 13.0, "lon": 80.2, "tags": {"amenity": "hospital"}} # valid
    ]
    parsed = list(ingestor.iter_parse_elements(elements, "Chennai", "hospital"))
    assert len(parsed) == 1
    assert parsed[0]["osm_id"] == 3
    assert parsed[0]["lat"] == 13.0
    assert parsed[0]["lon"] == 80.2
    assert parsed[0]["tags_json"] == {"amenity": "hospital"}


@pytest.mark.asyncio
async def test_osm_bulk_ingestor_fetch_stream():
    settings = MagicMock()
    ingestor = OSMBulkIngestor(settings)
    with patch.object(ingestor, "_query_overpass", new_callable=AsyncMock) as mock_query:
        mock_query.side_effect = [[{"osm_id": 1}], Exception("Timeout"), []] * 10
        batches = [batch async for batch in ingestor.fetch_stream()]
        assert len(batches) > 0
        assert batches[0] == [{"osm_id": 1}]


@pytest.mark.asyncio
async def test_admin_cache_endpoints():
    req = MagicMock(client=MagicMock(host="127.0.0.1"))
    user = {"sub": str(uuid.uuid4()), "role": "operator"}

    # Mock create_cache to test both with client and without client
    mock_cache = AsyncMock()
    mock_cache._client = AsyncMock()
    mock_cache._client.keys.return_value = ["waze:1", "waze:2"]

    with patch("core.redis_client.create_cache", return_value=mock_cache):
        status = await get_cache_status_admin(request=req, current_user=user)
        assert status == {"status": "online"}

        purge_res1 = await purge_cache_admin(request=req, key_prefix="waze", current_user=user)
        assert purge_res1["status"] == "success"
        mock_cache._client.keys.assert_called_with("waze*")
        mock_cache._client.delete.assert_called()

        purge_res2 = await purge_cache_admin(request=req, key_prefix=None, current_user=user)
        assert purge_res2["status"] == "success"
        mock_cache._client.flushdb.assert_called()

    # Test fallback / no client
    mock_cache_none = AsyncMock()
    mock_cache_none._client = None
    with patch("core.redis_client.create_cache", return_value=mock_cache_none):
        status_none = await get_cache_status_admin(request=req, current_user=user)
        assert status_none == {"status": "fallback_in_memory"}

        purge_none = await purge_cache_admin(request=req, key_prefix="waze", current_user=user)
        assert purge_none["status"] == "success"


@pytest.mark.asyncio
async def test_mcp_health_endpoint():
    res = await get_mcp_health()
    assert res["status"] == "healthy"
    assert res["mcp_server"] == "online"

    with patch("api.v1.mcp_server.mcp", MagicMock()) as mock_mcp:
        del mock_mcp._mcp_server
        # Force an exception by passing an object that raises when accessed
        with patch("api.v1.mcp_server.logger.exception") as mock_logger:
            with patch("api.v1.mcp_server.len", side_effect=Exception("Failure")):
                with pytest.raises(HTTPException) as exc_info:
                    await get_mcp_health()
                assert exc_info.value.status_code == 500


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
        res = await get_waze_cifs_feed(req, AsyncMock())
        assert res["note"] == "Rate limit exceeded. Token bucket depleted."


def test_admin_boundary_feature_validators():
    # Valid WKB and GeoJSON
    feat = AdminBoundaryFeature(
        id=1,
        code="TN01",
        name="Chennai",
        state_code="TN",
        geom_wkb="0101000020E6100000C1CA432B",
        geojson={"type": "Point", "coordinates": [80.2, 13.0]}
    )
    assert feat.geom_wkb == "0101000020E6100000C1CA432B"
    assert feat.geojson == {"type": "Point", "coordinates": [80.2, 13.0]}

    # Invalid WKB
    with pytest.raises(ValueError, match="Invalid WKB: must be a valid hex string"):
        AdminBoundaryFeature(id=1, code="TN01", name="Chennai", state_code="TN", geom_wkb="invalid_hex_wkb")

    # Invalid GeoJSON non-dict
    with pytest.raises(ValueError, match="Invalid GeoJSON: must be a dictionary"):
        AdminBoundaryFeature(id=1, code="TN01", name="Chennai", state_code="TN", geojson="not_a_dict")

    # Invalid GeoJSON missing fields
    with pytest.raises(ValueError, match="Invalid GeoJSON: missing 'type' or 'coordinates'"):
        AdminBoundaryFeature(id=1, code="TN01", name="Chennai", state_code="TN", geojson={"type": "Point"})

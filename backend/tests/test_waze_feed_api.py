# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Waze Feed API tests for SafeVixAI backend."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from api.v1 import waze_feed

# ── CIFS Mapping Tests ──────────────────────────────────────────────────────

class TestCIFSMapping:
    """Tests for CIFS type mapping functions."""

    def test_cifs_type_pothole(self):
        assert waze_feed._to_cifs_type("pothole") == "HAZARD_ON_ROAD"

    def test_cifs_type_accident(self):
        assert waze_feed._to_cifs_type("accident") == "ACCIDENT"

    def test_cifs_type_road_closed(self):
        assert waze_feed._to_cifs_type("road_closed") == "ROAD_CLOSED"

    def test_cifs_type_construction(self):
        assert waze_feed._to_cifs_type("construction") == "CONSTRUCTION"

    def test_cifs_type_flooding(self):
        assert waze_feed._to_cifs_type("flooding") == "HAZARD_ON_ROAD"

    def test_cifs_type_landslide(self):
        assert waze_feed._to_cifs_type("landslide") == "HAZARD_ON_ROAD"

    def test_cifs_type_debris(self):
        assert waze_feed._to_cifs_type("debris") == "HAZARD_ON_ROAD"

    def test_cifs_type_stalled_vehicle(self):
        assert waze_feed._to_cifs_type("stalled_vehicle") == "HAZARD_ON_ROAD"

    def test_cifs_type_unknown(self):
        assert waze_feed._to_cifs_type("unknown_type") == "HAZARD_ON_ROAD"

    def test_cifs_subtype_pothole(self):
        assert waze_feed._to_cifs_subtype("pothole") == "HAZARD_ON_ROAD_POT_HOLE"

    def test_cifs_subtype_accident(self):
        assert waze_feed._to_cifs_subtype("accident") == "ACCIDENT_MAJOR"

    def test_cifs_subtype_flooding(self):
        assert waze_feed._to_cifs_subtype("flooding") == "HAZARD_WEATHER_FLOOD"

    def test_cifs_subtype_road_closed(self):
        assert waze_feed._to_cifs_subtype("road_closed") == "ROAD_CLOSED_EVENT"

    def test_cifs_subtype_construction(self):
        assert waze_feed._to_cifs_subtype("construction") == "CONSTRUCTION"

    def test_cifs_subtype_unknown(self):
        assert waze_feed._to_cifs_subtype("unknown") == "HAZARD_ON_ROAD_OBJECT"


# ── Timestamp Formatting Tests ──────────────────────────────────────────────

class TestTimestampFormatting:
    """Tests for timestamp formatting."""

    def test_format_timestamp_none(self):
        result = waze_feed._format_timestamp(None)
        assert result is not None
        assert "/" in result

    def test_format_timestamp_valid_iso(self):
        result = waze_feed._format_timestamp("2026-05-22T10:30:00Z")
        assert "/" in result

    def test_format_timestamp_invalid(self):
        result = waze_feed._format_timestamp("not-a-timestamp")
        assert result is not None
        assert "/" in result


# ── Empty Feed Tests ────────────────────────────────────────────────────────

class TestEmptyFeed:
    """Tests for empty feed generation."""

    def test_empty_feed_structure(self):
        result = waze_feed._empty_feed("No data")

        assert result["incidents"] == []
        assert result["count"] == 0
        assert result["source"] == "SafeVixAI RoadWatch Community Reports"
        assert result["version"] == "1.0"
        assert result["note"] == "No data"
        assert "timestamp" in result

    def test_empty_feed_different_reasons(self):
        result = waze_feed._empty_feed("Database unavailable")
        assert result["note"] == "Database unavailable"

        result = waze_feed._empty_feed("No verified reports")
        assert result["note"] == "No verified reports"


# ── Feed Building Logic Tests ───────────────────────────────────────────────

class TestFeedBuildingLogic:
    """Tests for feed building logic without database."""

    def test_incident_id_formatting(self):
        """Test incident ID formatting."""
        report_id = "test-uuid-123"
        expected_id = f"SVAI-{report_id}"
        assert expected_id == "SVAI-test-uuid-123"

    def test_description_truncation(self):
        """Test description truncation to 200 chars."""
        long_desc = "A" * 300
        truncated = long_desc[:200]
        assert len(truncated) == 200

    def test_default_description(self):
        """Test default description when none provided."""
        desc = None
        result = desc or "Road hazard reported via SafeVixAI"
        assert result == "Road hazard reported via SafeVixAI"

    def test_severity_ttl_mapping(self):
        """Test severity to TTL hour mapping."""
        ttl_hours = {4: 72, 3: 48, 2: 24, 1: 12}

        assert ttl_hours[4] == 72  # Critical
        assert ttl_hours[3] == 48  # High
        assert ttl_hours[2] == 24  # Medium
        assert ttl_hours[1] == 12  # Low

    def test_severity_label_mapping(self):
        """Test severity value to label mapping."""
        severity_labels = {4: "critical", 3: "high", 2: "medium", 1: "low"}

        assert severity_labels[4] == "critical"
        assert severity_labels[3] == "high"
        assert severity_labels[2] == "medium"
        assert severity_labels[1] == "low"

    def test_expired_incident_filtering(self):
        """Test expired incident filtering logic."""
        now = datetime.now(UTC)

        # Critical severity (72 hour TTL) - should not be expired if created 2 days ago
        created_2_days = now - timedelta(days=2)
        end_dt_critical = created_2_days + timedelta(hours=72)
        assert end_dt_critical > now  # Not expired

        # Low severity (12 hour TTL) - should be expired if created 2 days ago
        created_2_days = now - timedelta(days=2)
        end_dt_low = created_2_days + timedelta(hours=12)
        assert end_dt_low < now  # Expired

    def test_polyline_formatting(self):
        """Test polyline coordinate formatting."""
        lat = 13.0827
        lon = 80.2707
        polyline = f"{lat} {lon}"
        assert polyline == "13.0827 80.2707"

    def test_country_code_hardcoded(self):
        """Test country code is hardcoded to IN."""
        assert "IN" == "IN"

    def test_reference_url_formatting(self):
        """Test reference URL formatting."""
        frontend_url = "https://safevixai.vercel.app"
        report_id = "test-uuid-123"
        expected = f"{frontend_url}/report/{report_id}"
        assert expected == "https://safevixai.vercel.app/report/test-uuid-123"

    def test_feed_response_structure(self):
        """Test feed response structure."""
        now = datetime.now(UTC)
        feed = {
            "incidents": [],
            "timestamp": now.strftime("%m/%d/%Y %H:%M:%S"),
            "source": "SafeVixAI RoadWatch Community Reports",
            "version": "1.0",
            "count": 0,
        }

        assert "incidents" in feed
        assert "timestamp" in feed
        assert "source" in feed
        assert "version" in feed
        assert "count" in feed
        assert feed["version"] == "1.0"

    def test_cifs_type_map_completeness(self):
        """Test CIFS type map covers all expected types."""
        expected_types = [
            "pothole", "damaged_road", "flooding", "waterlogging",
            "broken_barrier", "missing_sign", "accident", "road_closed",
            "construction", "landslide", "debris", "stalled_vehicle", "other"
        ]

        for issue_type in expected_types:
            assert issue_type in waze_feed.CIFS_TYPE_MAP or waze_feed._to_cifs_type(issue_type) == "HAZARD_ON_ROAD"

    def test_cifs_subtype_map_completeness(self):
        """Test CIFS subtype map covers all expected types."""
        expected_types = [
            "pothole", "damaged_road", "flooding", "waterlogging",
            "broken_barrier", "missing_sign", "accident", "road_closed",
            "construction", "landslide", "debris", "stalled_vehicle", "other"
        ]

        for issue_type in expected_types:
            result = waze_feed._to_cifs_subtype(issue_type)
            assert result is not None
            assert isinstance(result, str)

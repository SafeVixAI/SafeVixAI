# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from api.v1.waze_feed import (
    _empty_feed,
    _format_timestamp,
    _to_cifs_subtype,
    _to_cifs_type,
)


class TestCifsTypeMapping:
    def test_pothole_maps_to_hazard(self):
        assert _to_cifs_type("pothole") == "HAZARD_ON_ROAD"

    def test_accident_maps_to_accident(self):
        assert _to_cifs_type("accident") == "ACCIDENT"

    def test_road_closed_maps(self):
        assert _to_cifs_type("road_closed") == "ROAD_CLOSED"

    def test_construction_maps(self):
        assert _to_cifs_type("construction") == "CONSTRUCTION"

    def test_flooding_maps_to_weather_hazard(self):
        assert _to_cifs_type("flooding") == "HAZARD_ON_ROAD"

    def test_waterlogging_maps(self):
        assert _to_cifs_type("waterlogging") == "HAZARD_ON_ROAD"

    def test_damaged_road_maps(self):
        assert _to_cifs_type("damaged_road") == "HAZARD_ON_ROAD"

    def test_landslide_maps(self):
        assert _to_cifs_type("landslide") == "HAZARD_ON_ROAD"

    def test_debris_maps(self):
        assert _to_cifs_type("debris") == "HAZARD_ON_ROAD"

    def test_stalled_vehicle_maps(self):
        assert _to_cifs_type("stalled_vehicle") == "HAZARD_ON_ROAD"

    def test_unknown_defaults_to_hazard(self):
        assert _to_cifs_type("unknown_type") == "HAZARD_ON_ROAD"

    def test_case_insensitive(self):
        assert _to_cifs_type("Pothole") == "HAZARD_ON_ROAD"

    def test_space_normalized(self):
        assert _to_cifs_type("road closed") == "ROAD_CLOSED"


class TestCifsSubtypeMapping:
    def test_pothole_subtype(self):
        assert _to_cifs_subtype("pothole") == "HAZARD_ON_ROAD_POT_HOLE"

    def test_accident_subtype(self):
        assert _to_cifs_subtype("accident") == "ACCIDENT_MAJOR"

    def test_road_closed_subtype(self):
        assert _to_cifs_subtype("road_closed") == "ROAD_CLOSED_EVENT"

    def test_construction_subtype(self):
        assert _to_cifs_subtype("construction") == "CONSTRUCTION"

    def test_flooding_subtype(self):
        assert _to_cifs_subtype("flooding") == "HAZARD_WEATHER_FLOOD"

    def test_waterlogging_subtype(self):
        assert _to_cifs_subtype("waterlogging") == "HAZARD_WEATHER_FLOOD"

    def test_missing_sign_subtype(self):
        assert _to_cifs_subtype("missing_sign") == "HAZARD_ON_ROAD_MISSING_SIGN"

    def test_unknown_defaults(self):
        assert _to_cifs_subtype("unknown") == "HAZARD_ON_ROAD_OBJECT"


class TestTimestampFormatting:
    def test_formats_iso_timestamp(self):
        result = _format_timestamp("2026-05-18T10:30:00Z")
        assert "05/18/2026" in result

    def test_handles_none(self):
        result = _format_timestamp(None)
        assert isinstance(result, str)
        assert "/" in result

    def test_handles_invalid_string(self):
        result = _format_timestamp("not-a-date")
        assert isinstance(result, str)


class TestEmptyFeed:
    def test_empty_feed_structure(self):
        feed = _empty_feed("test reason")

        assert feed["incidents"] == []
        assert feed["count"] == 0
        assert feed["version"] == "1.0"
        assert feed["source"] == "SafeVixAI RoadWatch Community Reports"
        assert feed["note"] == "test reason"
        assert "timestamp" in feed

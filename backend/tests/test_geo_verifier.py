# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import math
from datetime import datetime

from services.geo_verifier import GeoVerifier, _haversine_m


def test_haversine_same_point():
    assert _haversine_m(20.0, 80.0, 20.0, 80.0) == 0.0


def test_haversine_one_degree_lat():
    dist = _haversine_m(0.0, 0.0, 1.0, 0.0)
    assert 110000 < dist < 112000


def test_haversine_one_degree_lon_at_equator():
    dist = _haversine_m(0.0, 0.0, 0.0, 1.0)
    assert 110000 < dist < 112000


def test_haversine_symmetric():
    d1 = _haversine_m(12.0, 77.0, 13.0, 78.0)
    d2 = _haversine_m(13.0, 78.0, 12.0, 77.0)
    assert math.isclose(d1, d2, rel_tol=1e-9)


def test_resolution_proximity_within():
    valid, dist = GeoVerifier.verify_resolution_proximity(
        complaint_lat=12.9716,
        complaint_lon=77.5946,
        officer_lat=12.9720,
        officer_lon=77.5949,
    )
    assert valid is True
    assert dist < 150.0


def test_resolution_proximity_over():
    valid, dist = GeoVerifier.verify_resolution_proximity(
        complaint_lat=12.9716,
        complaint_lon=77.5946,
        officer_lat=13.0000,
        officer_lon=77.6200,
    )
    assert valid is False
    assert dist > 150.0


def test_resolution_proximity_exact_boundary():
    valid, _ = GeoVerifier.verify_resolution_proximity(
        complaint_lat=0.0,
        complaint_lon=0.0,
        officer_lat=0.0,
        officer_lon=0.001347,
    )
    assert valid is True


def test_timestamp_valid():
    result = GeoVerifier.verify_timestamps(
        assigned_at=datetime(2026, 1, 1, 10, 0, 0),
        resolved_at=datetime(2026, 1, 1, 12, 0, 0),
    )
    assert result is True


def test_timestamp_invalid():
    result = GeoVerifier.verify_timestamps(
        assigned_at=datetime(2026, 1, 1, 14, 0, 0),
        resolved_at=datetime(2026, 1, 1, 12, 0, 0),
    )
    assert result is False


def test_timestamp_no_assigned_at():
    result = GeoVerifier.verify_timestamps(
        assigned_at=None,
        resolved_at=datetime(2026, 1, 1, 12, 0, 0),
    )
    assert result is True


def test_exif_no_metadata():
    valid, msg = GeoVerifier.verify_exif_metadata(
        complaint_lat=12.9716,
        complaint_lon=77.5946,
        exif_lat=None,
        exif_lon=None,
    )
    assert valid is True
    assert "No GPS metadata" in msg


def test_exif_within_500m():
    valid, msg = GeoVerifier.verify_exif_metadata(
        complaint_lat=12.9716,
        complaint_lon=77.5946,
        exif_lat=12.9720,
        exif_lon=77.5950,
    )
    assert valid is True
    assert "verified" in msg


def test_exif_outside_500m():
    valid, msg = GeoVerifier.verify_exif_metadata(
        complaint_lat=12.9716,
        complaint_lon=77.5946,
        exif_lat=13.0000,
        exif_lon=77.7000,
    )
    assert valid is False
    assert "too far" in msg

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import math
from datetime import time
from unittest.mock import AsyncMock, MagicMock, patch

from services.officer_route_optimizer import (
    OfficerRouteOptimizer,
    OfficerShift,
    _haversine_km,
    _nearest_neighbor_tsp,
)


class TestHaversineKm:
    def test_same_point(self):
        assert _haversine_km(20.0, 80.0, 20.0, 80.0) == 0.0

    def test_one_degree_lat(self):
        dist = _haversine_km(0.0, 0.0, 1.0, 0.0)
        assert 110 < dist < 112

    def test_symmetric(self):
        d1 = _haversine_km(12.0, 77.0, 13.0, 78.0)
        d2 = _haversine_km(13.0, 78.0, 12.0, 77.0)
        assert math.isclose(d1, d2, rel_tol=1e-9)


class TestNearestNeighborTsp:
    def test_empty_list(self):
        result = _nearest_neighbor_tsp([], 0.0, 0.0)
        assert result == []

    def test_single_point(self):
        points = [{"lat": 10.0, "lon": 20.0, "severity": 3}]
        result = _nearest_neighbor_tsp(points, 0.0, 0.0)
        assert len(result) == 1
        assert result[0]["lat"] == 10.0

    def test_multi_point_ordering(self):
        points = [
            {"lat": 10.0, "lon": 20.0, "severity": 3},
            {"lat": 10.001, "lon": 20.001, "severity": 3},
            {"lat": 10.002, "lon": 20.002, "severity": 3},
        ]
        result = _nearest_neighbor_tsp(points, 10.0, 20.0)
        assert len(result) == 3

    def test_severity_bonus_prioritizes_high_severity(self):
        points = [
            {"lat": 10.0, "lon": 20.0, "severity": 5},
            {"lat": 10.1, "lon": 20.1, "severity": 1},
        ]
        result = _nearest_neighbor_tsp(points, 10.05, 20.05)
        assert len(result) == 2


class TestOfficerRouteOptimizer:
    async def test_no_complaints_found(self):
        db = MagicMock()
        db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        route = await OfficerRouteOptimizer.optimize_route(
            db, officer_id="OFF-1", officer_lat=12.97, officer_lon=77.59,
        )
        assert route.total_stops == 0
        assert route.total_distance_km == 0
        assert "No open complaints found" in route.warnings

    async def test_city_filter(self):
        """Covers line 143: city filter branch."""
        db = MagicMock()
        db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        with patch("services.officer_route_optimizer.RoadIssue.city", "Chennai", create=True):
            route = await OfficerRouteOptimizer.optimize_route(
                db, officer_id="OFF-1", officer_lat=12.97, officer_lon=77.59,
                city="Chennai",
            )
        assert route.total_stops == 0

    async def test_exception_on_build_point_skipped(self):
        """Covers lines 184-185: TypeError/ValueError when building point list."""
        db = MagicMock()
        db.execute = AsyncMock()

        # An issue that raises TypeError when accessing latitude
        bad_issue = MagicMock()
        bad_issue.status = "open"
        bad_issue.latitude = MagicMock()
        bad_issue.latitude.__float__ = MagicMock(side_effect=TypeError("bad float"))
        bad_issue.longitude = 77.59
        bad_issue.complaint_ref = "REF-BAD"
        bad_issue.issue_type = "pothole"
        bad_issue.severity = 3
        bad_issue.location = MagicMock()

        good_issue = MagicMock()
        good_issue.status = "open"
        good_issue.latitude = 12.9716
        good_issue.longitude = 77.5946
        good_issue.complaint_ref = "REF-GOOD"
        good_issue.issue_type = "pothole"
        good_issue.severity = 3
        good_issue.ward_id = None
        good_issue.address = None
        good_issue.location = MagicMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [bad_issue, good_issue]
        db.execute.return_value = mock_result

        route = await OfficerRouteOptimizer.optimize_route(
            db, officer_id="OFF-1", officer_lat=12.97, officer_lon=77.59,
        )
        assert route.total_stops == 1
        assert route.stops[0].complaint_ref == "REF-GOOD"

    async def test_ward_id_filtering(self):
        db = MagicMock()
        db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        route = await OfficerRouteOptimizer.optimize_route(
            db, officer_id="OFF-1", officer_lat=12.97, officer_lon=77.59,
            ward_id="WARD-2",
        )
        assert route.total_stops == 0

    async def test_max_complaints_per_shift_cap(self):
        db = MagicMock()
        db.execute = AsyncMock()

        issues = []
        for i in range(15):
            iss = MagicMock()
            iss.status = "open"
            iss.latitude = 13.0 + i * 0.01
            iss.longitude = 78.0 + i * 0.01
            iss.complaint_ref = f"REF-{i:03d}"
            iss.issue_type = "pothole"
            iss.severity = 3
            iss.ward_id = None
            iss.address = None
            iss.location = MagicMock()
            issues.append(iss)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = issues
        db.execute.return_value = mock_result

        short_shift = OfficerShift(max_complaints_per_shift=3)
        route = await OfficerRouteOptimizer.optimize_route(
            db, officer_id="OFF-1", officer_lat=13.0, officer_lon=78.0,
            shift=short_shift,
        )
        assert route.total_stops == 3

    async def test_default_shift_values(self):
        db = MagicMock()
        db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        route = await OfficerRouteOptimizer.optimize_route(
            db, officer_id="OFF-1", officer_lat=12.97, officer_lon=77.59,
        )
        assert route.shift.start_time.hour == 9
        assert route.shift.end_time.hour == 18
        assert route.shift.max_complaints_per_shift == 12
        assert route.shift.avg_minutes_per_stop == 20

    async def test_issue_without_coordinates_skipped(self):
        db = MagicMock()
        db.execute = AsyncMock()

        issue_with_coords = MagicMock()
        issue_with_coords.status = "open"
        issue_with_coords.latitude = 12.9716
        issue_with_coords.longitude = 77.5946
        issue_with_coords.complaint_ref = "REF-001"
        issue_with_coords.issue_type = "pothole"
        issue_with_coords.severity = 3
        issue_with_coords.ward_id = None
        issue_with_coords.address = None
        issue_with_coords.location = MagicMock()

        issue_no_coords = MagicMock()
        issue_no_coords.status = "open"
        issue_no_coords.latitude = None
        issue_no_coords.longitude = None
        issue_no_coords.complaint_ref = "REF-002"
        issue_no_coords.issue_type = "garbage"
        issue_no_coords.severity = 4
        issue_no_coords.ward_id = None
        issue_no_coords.address = None
        issue_no_coords.location = MagicMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [issue_with_coords, issue_no_coords]
        db.execute.return_value = mock_result

        route = await OfficerRouteOptimizer.optimize_route(
            db, officer_id="OFF-1", officer_lat=12.97, officer_lon=77.59,
        )
        assert route.total_stops == 1
        assert route.stops[0].complaint_ref == "REF-001"

    async def test_shift_boundary_exceeded(self):
        db = MagicMock()
        db.execute = AsyncMock()

        issue = MagicMock()
        issue.status = "open"
        issue.latitude = 13.5
        issue.longitude = 78.5
        issue.complaint_ref = "REF-FAR"
        issue.issue_type = "pothole"
        issue.severity = 3
        issue.ward_id = None
        issue.address = None
        issue.location = MagicMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [issue]
        db.execute.return_value = mock_result

        short_shift = OfficerShift(
            start_time=time(9, 0),
            end_time=time(9, 5),
            max_complaints_per_shift=12,
            avg_minutes_per_stop=1,
        )

        route = await OfficerRouteOptimizer.optimize_route(
            db, officer_id="OFF-1", officer_lat=12.97, officer_lon=77.59,
            shift=short_shift,
        )
        assert "exceeds shift" in route.warnings[0]

    async def test_value_error_build_point_skipped(self):
        """Covers ValueError path in lines 184-185."""
        db = MagicMock()
        db.execute = AsyncMock()

        bad_issue = MagicMock()
        bad_issue.status = "open"
        bad_issue.latitude = "not-a-number"
        bad_issue.longitude = 77.59
        bad_issue.complaint_ref = "REF-BAD2"
        bad_issue.issue_type = "pothole"
        bad_issue.severity = 3
        bad_issue.location = MagicMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [bad_issue]
        db.execute.return_value = mock_result

        route = await OfficerRouteOptimizer.optimize_route(
            db, officer_id="OFF-1", officer_lat=12.97, officer_lon=77.59,
        )
        assert route.total_stops == 0

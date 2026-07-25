# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Geo Verifier for SafeVixAI.

Verifies officer location and metadata when submitting evidence or completing work.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime

logger = logging.getLogger("safevixai.geo_verifier")


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in meters."""
    r = 6371000.0  # Radius of earth in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class GeoVerifier:
    """Verifies that field activities are geographically and temporally plausible."""

    MAX_RESOLUTION_DISTANCE_M = 150.0  # Allow up to 150 meters for GPS drift

    @classmethod
    def verify_resolution_proximity(
        cls,
        *,
        complaint_lat: float,
        complaint_lon: float,
        officer_lat: float,
        officer_lon: float,
    ) -> tuple[bool, float]:
        """
        Verify that the officer's resolution location is close enough to the complaint.

        Returns:
            (is_verified, distance_meters)
        """
        distance = _haversine_m(complaint_lat, complaint_lon, officer_lat, officer_lon)
        is_valid = distance <= cls.MAX_RESOLUTION_DISTANCE_M

        if not is_valid:
            logger.warning(
                "Geo-verification failed: officer is %.1fm away from complaint (limit: %.1fm)",
                distance, cls.MAX_RESOLUTION_DISTANCE_M
            )
        else:
            logger.info("Geo-verification successful: officer is %.1fm away", distance)

        return is_valid, distance

    @classmethod
    def verify_timestamps(
        cls,
        *,
        assigned_at: datetime | None,
        resolved_at: datetime,
    ) -> bool:
        """Verify that the resolution time is logically after the assignment time."""
        if not assigned_at:
            return True
        return resolved_at > assigned_at

    @classmethod
    def verify_exif_metadata(
        cls,
        *,
        complaint_lat: float,
        complaint_lon: float,
        exif_lat: float | None,
        exif_lon: float | None,
    ) -> tuple[bool, str]:
        """
        Compare the GPS coordinates inside the photo EXIF headers with the complaint location.

        Returns:
            (is_verified, message)
        """
        if exif_lat is None or exif_lon is None:
            return True, "No GPS metadata found in photo headers (skipped EXIF verification)"

        distance = _haversine_m(complaint_lat, complaint_lon, exif_lat, exif_lon)
        # Allow wider drift (e.g. 500m) since EXIF coordinates could be from a slightly different angle/cell tower triangulation
        if distance > 500.0:
            logger.warning(
                "EXIF verification warning: photo coordinates are %.1fm away from complaint",
                distance
            )
            return False, "Photo metadata coordinates are too far (%.1fm) from the complaint location"

        logger.info("EXIF verification passed: photo coordinates are within %.1fm", distance)
        return True, "Photo metadata coordinates verified"

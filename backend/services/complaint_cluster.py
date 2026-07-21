# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Spatial clustering service using DBSCAN for road issue hotspot detection.

Provides DBSCAN-based spatial clustering on road issue locations to detect
hotspots, identify duplicate clusters, and generate cluster-level analytics.
"""

from __future__ import annotations

import logging
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.road_issue import RoadIssue

logger = logging.getLogger(__name__)


@dataclass
class SpatialCluster:
    """Represents a discovered spatial cluster of complaints."""
    cluster_id: int
    centroid_lat: float
    centroid_lon: float
    point_count: int
    radius_meters: float
    dominant_issue_type: str
    avg_severity: float
    issue_uuids: list[str] = field(default_factory=list)
    issue_types: dict[str, int] = field(default_factory=dict)


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in meters."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def dbscan_cluster(
    points: list[dict[str, Any]],
    eps_meters: float = 200,
    min_samples: int = 3,
) -> list[SpatialCluster]:
    """
    Pure-Python DBSCAN implementation for spatial complaint clustering.
    
    No sklearn dependency — works on any machine.
    
    Args:
        points: list of dicts with 'lat', 'lon', 'uuid', 'issue_type', 'severity'
        eps_meters: neighborhood radius in meters (default 200m)
        min_samples: minimum points to form a cluster (default 3)
    
    Returns:
        list of SpatialCluster objects
    """
    n = len(points)
    if n == 0:
        return []

    labels = [-1] * n  # -1 = noise
    visited = [False] * n
    cluster_id = 0

    def _region_query(idx: int) -> list[int]:
        neighbors = []
        p = points[idx]
        for j in range(n):
            if j == idx:
                continue
            q = points[j]
            if _haversine(p['lat'], p['lon'], q['lat'], q['lon']) <= eps_meters:
                neighbors.append(j)
        return neighbors

    for i in range(n):
        if visited[i]:
            continue
        visited[i] = True
        neighbors = _region_query(i)

        if len(neighbors) < min_samples - 1:
            # Noise
            labels[i] = -1
            continue

        # Start new cluster
        labels[i] = cluster_id
        seed_set = list(neighbors)
        j = 0
        while j < len(seed_set):
            q = seed_set[j]
            if not visited[q]:
                visited[q] = True
                q_neighbors = _region_query(q)
                if len(q_neighbors) >= min_samples - 1:
                    seed_set.extend([x for x in q_neighbors if x not in seed_set])
            if labels[q] == -1:
                labels[q] = cluster_id
            j += 1

        cluster_id += 1

    # Build cluster objects
    cluster_map: dict[int, list[int]] = {}
    for idx, lbl in enumerate(labels):
        if lbl >= 0:
            cluster_map.setdefault(lbl, []).append(idx)

    clusters = []
    for cid, indices in cluster_map.items():
        lats = [points[i]['lat'] for i in indices]
        lons = [points[i]['lon'] for i in indices]
        severities = [points[i].get('severity', 3) for i in indices]
        types = [points[i].get('issue_type', 'unknown') for i in indices]
        uuids = [str(points[i].get('uuid', '')) for i in indices]

        centroid_lat = sum(lats) / len(lats)
        centroid_lon = sum(lons) / len(lons)

        # Max distance from centroid = radius
        max_dist = max(
            _haversine(centroid_lat, centroid_lon, lat, lon)
            for lat, lon in zip(lats, lons)
        )

        type_counts = Counter(types)
        dominant = type_counts.most_common(1)[0][0]

        clusters.append(SpatialCluster(
            cluster_id=cid,
            centroid_lat=round(centroid_lat, 6),
            centroid_lon=round(centroid_lon, 6),
            point_count=len(indices),
            radius_meters=round(max_dist, 1),
            dominant_issue_type=dominant,
            avg_severity=round(sum(severities) / len(severities), 2),
            issue_uuids=uuids,
            issue_types=dict(type_counts),
        ))

    clusters.sort(key=lambda c: c.point_count, reverse=True)
    return clusters


class ComplaintClusterService:
    """Service for spatial complaint clustering and hotspot detection."""

    @staticmethod
    async def find_clusters(
        db: AsyncSession,
        *,
        city: str | None = None,
        ward_id: str | None = None,
        eps_meters: float = 200,
        min_samples: int = 3,
        status_filter: list[str] | None = None,
    ) -> list[SpatialCluster]:
        """
        Find complaint clusters using DBSCAN spatial clustering.
        
        Args:
            db: database session
            city: filter by city name
            ward_id: filter by ward id
            eps_meters: cluster radius in meters
            min_samples: minimum complaints per cluster
            status_filter: list of statuses to include
        
        Returns:
            list of SpatialCluster objects sorted by point_count descending
        """
        if status_filter is None:
            status_filter = ["open", "acknowledged", "in_progress"]

        stmt = (
            select(
                RoadIssue.uuid,
                func.ST_Y(RoadIssue.location).label('lat'),
                func.ST_X(RoadIssue.location).label('lon'),
                RoadIssue.issue_type,
                RoadIssue.severity,
            )
            .where(RoadIssue.status.in_(status_filter))
            .where(RoadIssue.location.isnot(None))
        )

        if city:
            stmt = stmt.where(RoadIssue.city == city)
        if ward_id:
            stmt = stmt.where(RoadIssue.ward_id == ward_id)

        result = await db.execute(stmt)
        rows = result.all()

        if len(rows) < min_samples:
            return []

        points = [
            {
                'lat': row.lat,
                'lon': row.lon,
                'uuid': str(row.uuid),
                'issue_type': row.issue_type or 'unknown',
                'severity': row.severity or 3,
            }
            for row in rows
            if row.lat is not None and row.lon is not None
        ]

        clusters = dbscan_cluster(points, eps_meters=eps_meters, min_samples=min_samples)
        logger.info(
            "Found %d clusters from %d complaints (eps=%dm, min=%d)",
            len(clusters), len(points), eps_meters, min_samples,
        )
        return clusters

    @staticmethod
    async def get_hotspots(
        db: AsyncSession,
        *,
        city: str | None = None,
        top_n: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Get top N complaint hotspots for a city.
        
        Returns simplified dict format suitable for API responses.
        """
        clusters = await ComplaintClusterService.find_clusters(
            db, city=city, eps_meters=300, min_samples=3
        )
        return [
            {
                'cluster_id': c.cluster_id,
                'lat': c.centroid_lat,
                'lon': c.centroid_lon,
                'complaint_count': c.point_count,
                'radius_m': c.radius_meters,
                'dominant_type': c.dominant_issue_type,
                'avg_severity': c.avg_severity,
                'issue_types': c.issue_types,
            }
            for c in clusters[:top_n]
        ]

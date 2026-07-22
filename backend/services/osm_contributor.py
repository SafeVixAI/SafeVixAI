# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""
osm_contributor.py — OpenStreetMap Contribution Service

Pushes verified RoadWatch reports to OpenStreetMap via the OSM API v0.6.
Creates hazard nodes with appropriate tags so the data appears in all
OSM-based maps (MapLibre, Apple Maps refresh, HERE Maps, etc).

Requirements:
    - OSM bot account registered on openstreetmap.org
    - OAuth 2.0 credentials (client_id, client_secret, access_token)
    - Only verified reports (2+ confirmations) are contributed

OSM API Docs: https://wiki.openstreetmap.org/wiki/API_v0.6
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


# ── OSM Tag Mapping ───────────────────────────────────────────────────────────

OSM_TAG_MAP: dict[str, dict[str, str]] = {
    "pothole": {
        "highway": "pothole",
        "surface": "damaged",
        "hazard": "yes",
        "hazard:type": "pothole",
    },
    "damaged_road": {
        "surface": "damaged",
        "hazard": "yes",
        "hazard:type": "road_damage",
    },
    "flooding": {
        "hazard": "yes",
        "hazard:type": "flood",
        "flood_prone": "yes",
    },
    "waterlogging": {
        "hazard": "yes",
        "hazard:type": "flood",
        "flood_prone": "yes",
    },
    "broken_barrier": {
        "barrier": "damaged",
        "hazard": "yes",
        "hazard:type": "broken_barrier",
    },
    "missing_sign": {
        "traffic_sign": "missing",
        "hazard": "yes",
        "hazard:type": "missing_sign",
    },
    "accident": {
        "hazard": "yes",
        "hazard:type": "accident",
        "accident:blackspot": "yes",
    },
    "landslide": {
        "hazard": "yes",
        "hazard:type": "landslide",
        "natural": "landslide",
    },
    "debris": {
        "hazard": "yes",
        "hazard:type": "debris",
    },
}


# ── OSM Contributor ───────────────────────────────────────────────────────────


class OSMContributor:
    """
    Manages OpenStreetMap contributions for verified road reports.

    This service:
    1. Opens a changeset
    2. Creates a node with hazard tags
    3. Closes the changeset

    All operations are attributed to the SafeVixAI bot account.
    """

    OSM_API_BASE = "https://api.openstreetmap.org/api/0.6"

    def __init__(
        self,
        access_token: str | None = None,
    ) -> None:
        self._access_token = access_token or self._load_token()
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "text/xml",
                "User-Agent": "SafeVixAI-RoadWatch/1.0",
            },
        )

    @staticmethod
    def _load_token() -> str:
        """Load OSM access token from environment."""
        import os

        token = os.getenv("OSM_ACCESS_TOKEN", "")
        if not token:
            logger.warning("OSM_ACCESS_TOKEN not set — contributions will be disabled", extra={"service": "osm_contributor"})
        return token

    @property
    def is_configured(self) -> bool:
        """Check if OSM contribution is available."""
        return bool(self._access_token)

    async def contribute_report(
        self,
        report: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Push a verified road report to OpenStreetMap.

        Args:
            report: Road report dict with id, lat, lon, issue_type, description,
                    road_name, city, severity, etc.

        Returns:
            Dict with status, changeset_id, node_id, or error details.
        """
        if not self.is_configured:
            return {"status": "skipped", "reason": "OSM not configured"}

        lat = report.get("lat")
        lon = report.get("lon")
        issue_type = report.get("issue_type", "other")

        if not lat or not lon:
            return {"status": "error", "reason": "Missing coordinates"}

        # Get tags for this issue type
        base_tags = OSM_TAG_MAP.get(
            issue_type.lower().replace(" ", "_"),
            {"hazard": "yes"},
        )

        # Add common tags
        tags: dict[str, str] = {
            **base_tags,
            "source": "SafeVixAI_RoadWatch_v1",
            "source:date": datetime.now(UTC).strftime("%Y-%m-%d"),
            "note": f"Community-reported via SafeVixAI RoadWatch (ID: {report.get('id', 'N/A')})",
            "fixme": "Verify on ground — community report",
        }

        # Optional tags
        if report.get("description"):
            tags["description"] = report["description"][:255]
        if report.get("road_name"):
            tags["name"] = report["road_name"]

        try:
            # Step 1: Open changeset
            changeset_id = await self._open_changeset(issue_type)
            if not changeset_id:
                return {"status": "error", "reason": "Failed to open changeset"}

            # Step 2: Create node
            node_id = await self._create_node(changeset_id, lat, lon, tags)
            if not node_id:
                await self._close_changeset(changeset_id)
                return {"status": "error", "reason": "Failed to create node"}

            # Step 3: Close changeset
            await self._close_changeset(changeset_id)

            logger.info(
                "OSM contribution success: changeset=%s node=%s type=%s",
                changeset_id,
                node_id,
                issue_type,
                extra={"service": "osm_contributor"},
            )

            return {
                "status": "success",
                "changeset_id": changeset_id,
                "node_id": node_id,
                "osm_url": f"https://www.openstreetmap.org/node/{node_id}",
            }

        except httpx.HTTPError as exc:
            logger.error("OSM contribution failed: %s", exc, extra={"service": "osm_contributor"})
            return {"status": "error", "reason": str(exc)}

    async def _open_changeset(self, issue_type: str) -> str | None:
        """Open a new OSM changeset."""
        xml = f"""
        <osm>
          <changeset>
            <tag k="created_by" v="SafeVixAI RoadWatch v1.0"/>
            <tag k="comment" v="SafeVixAI: {issue_type} report from community"/>
            <tag k="source" v="SafeVixAI community road reports"/>
            <tag k="bot" v="yes"/>
          </changeset>
        </osm>
        """.strip()

        try:
            resp = await self._client.put(
                f"{self.OSM_API_BASE}/changeset/create",
                content=xml,
            )
            if resp.status_code == 200:
                return resp.text.strip()
            logger.warning("OSM changeset open failed: %d %s", resp.status_code, resp.text, extra={"service": "osm_contributor"})
            return None
        except httpx.HTTPError as exc:
            logger.error("OSM changeset open error: %s", exc, extra={"service": "osm_contributor"})
            return None

    async def _create_node(
        self,
        changeset_id: str,
        lat: float,
        lon: float,
        tags: dict[str, str],
    ) -> str | None:
        """Create a node in the given changeset."""
        tags_xml = "\n".join(
            f'    <tag k="{k}" v="{v}"/>' for k, v in tags.items()
        )

        xml = f"""
        <osm>
          <node changeset="{changeset_id}" lat="{lat}" lon="{lon}">
        {tags_xml}
          </node>
        </osm>
        """.strip()

        try:
            resp = await self._client.put(
                f"{self.OSM_API_BASE}/node/create",
                content=xml,
            )
            if resp.status_code == 200:
                return resp.text.strip()
            logger.warning("OSM node create failed: %d %s", resp.status_code, resp.text, extra={"service": "osm_contributor"})
            return None
        except httpx.HTTPError as exc:
            logger.error("OSM node create error: %s", exc, extra={"service": "osm_contributor"})
            return None

    async def _close_changeset(self, changeset_id: str) -> bool:
        """Close an OSM changeset."""
        try:
            resp = await self._client.put(
                f"{self.OSM_API_BASE}/changeset/{changeset_id}/close",
            )
            return resp.status_code == 200
        except httpx.HTTPError as exc:
            logger.error("OSM changeset close error: %s", exc, extra={"service": "osm_contributor"})
            return False

    async def close(self) -> None:
        """Clean up HTTP client."""
        await self._client.aclose()


# ── Singleton ──────────────────────────────────────────────────────────────────

_contributor: OSMContributor | None = None


def get_osm_contributor() -> OSMContributor:
    """Get or create the singleton OSM contributor instance."""
    global _contributor
    if _contributor is None:
        _contributor = OSMContributor()
    return _contributor

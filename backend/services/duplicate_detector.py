# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import logging
import uuid

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.road_issue import RoadIssue

logger = logging.getLogger(__name__)


class DuplicateDetector:
    @staticmethod
    async def find_duplicates(
        db: AsyncSession,
        *,
        lat: float,
        lon: float,
        issue_type: str,
        radius_meters: int = 100
    ) -> list[RoadIssue]:
        """
        Find open issues of the same type (or general category) within radius_meters.
        Returns a list of matching RoadIssue records.
        """
        point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        point_geography = cast(point, Geography)
        issue_geography = cast(RoadIssue.location, Geography)

        # Query active issues (open, acknowledged, in_progress) of same type within radius
        stmt = (
            select(RoadIssue)
            .where(func.ST_DWithin(issue_geography, point_geography, radius_meters))
            .where(RoadIssue.status.in_(["open", "acknowledged", "in_progress"]))
            .where(RoadIssue.issue_type == issue_type)
            .where(RoadIssue.duplicate_of_uuid.is_(None)) # Only match primary reports
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def increment_confirmation(db: AsyncSession, issue_uuid: uuid.UUID) -> RoadIssue | None:
        """
        Upvote/confirm an issue by a citizen to increase confidence and prevent duplication.
        """
        stmt = select(RoadIssue).where(RoadIssue.uuid == issue_uuid)
        result = await db.execute(stmt)
        issue = result.scalar_one_or_none()

        if issue:
            issue.confirmation_count += 1
            # Autoacknowledged if confirmation count exceeds threshold (e.g. 5 upvotes)
            if issue.status == "open" and issue.confirmation_count >= 5:
                issue.status = "acknowledged"
            await db.commit()
            await db.refresh(issue)

        return issue

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.road_issue import RoadIssue
from services.complaint_lifecycle import ComplaintLifecycle

logger = logging.getLogger(__name__)


class SLAMonitor:
    def __init__(self, session_maker: async_sessionmaker[AsyncSession] | None = None) -> None:
        self.session_maker = session_maker
        self.is_running = False

    async def check_slas(self, db: AsyncSession) -> int:
        """
        Scan all active unresolved complaints (status is NOT 'resolved' or 'rejected')
        where sla_deadline is in the past, and escalate them.
        """
        now = datetime.now(UTC).replace(tzinfo=None)

        # Query active issues with breached SLA
        stmt = (
            select(RoadIssue)
            .where(RoadIssue.status.in_(["open", "acknowledged", "in_progress"]))
            .where(RoadIssue.sla_deadline.is_not(None))
            .where(RoadIssue.sla_deadline < now)
        )

        result = await db.execute(stmt)
        breached_issues = result.scalars().all()

        escalated_count = 0
        for issue in breached_issues:
            # Check if already escalated to prevent duplicate event spamming
            timeline = await ComplaintLifecycle.get_timeline(db, issue.uuid)
            already_escalated = any(e.event_type == "escalated" and "SLA breach" in (e.notes or "") for e in timeline)

            if not already_escalated:
                logger.warning(
                    "Complaint %s breached SLA. SLA Deadline: %s. Escalating...",
                    issue.complaint_ref, issue.sla_deadline,
                    extra={"service": "sla_monitor", "complaint_ref": issue.complaint_ref}
                )
                try:
                    await ComplaintLifecycle.escalate(
                        db,
                        complaint_uuid=issue.uuid,
                        reason=f"SLA breach: Resolved deadline ({issue.sla_deadline}) has passed."
                    )
                    escalated_count += 1

                    # Send email/webhook notification
                    try:
                        from services.sla_notification import SLANotificationService
                        notifier = SLANotificationService()
                        await notifier.notify_sla_breach(
                            complaint_ref=issue.complaint_ref,
                            issue_type=issue.issue_type or 'unknown',
                            severity=issue.severity or 3,
                            city=getattr(issue, 'city', None),
                            ward_id=getattr(issue, 'ward_id', None),
                            sla_deadline=issue.sla_deadline,
                        )
                    except Exception as notify_err:
                        logger.debug("SLA notification skipped: %s", notify_err)

                except Exception:
                    logger.exception("Failed to escalate %s", issue.uuid)

        return escalated_count

    async def start_loop(self, interval_seconds: int = 900) -> None:
        """Start the background check loop."""
        if not self.session_maker:
            logger.error("Cannot start SLA loop: session_maker is None")
            return

        self.is_running = True
        logger.info("SLA Monitor background loop started. Interval: %ss", interval_seconds)

        while self.is_running:
            try:
                await asyncio.sleep(interval_seconds)
                async with self.session_maker() as db:
                    escalated = await self.check_slas(db)
                    if escalated > 0:
                        logger.info("SLA Monitor loop escalated %d complaints.", escalated)
            except asyncio.CancelledError:
                logger.info("SLA Monitor background loop cancelled.")
                break
            except Exception:
                logger.exception("Error in SLA Monitor loop")

    def stop(self) -> None:
        """Stop the background check loop."""
        self.is_running = False
        logger.info("SLA Monitor background loop stop requested.")

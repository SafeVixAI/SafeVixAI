# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import hashlib
import logging
import random
import string
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.metrics import issue_reports_total, issue_sla_breaches_total
from models.issue_report import IssueReport
from models.issue_timeline import IssueTimelineEvent
from models.schemas_issues import (
    CreateIssueRequest,
    IssueDetail,
    IssueListItem,
    IssueListResponse,
    IssueStatsResponse,
    IssueStatus,
    TimelineEvent,
    UpdateIssueRequest,
)

logger = logging.getLogger(__name__)

settings = get_settings()


def _generate_tracking_number() -> str:
    prefix = 'SAFE'
    ts = datetime.now(UTC).strftime('%y%m%d')
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f'{prefix}-{ts}-{rand}'


def _compute_text_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]


class IssueService:
    def __init__(self) -> None:
        self._spam_hashes: set[str] = set()

    async def create_issue(
        self,
        *,
        db: AsyncSession,
        request: CreateIssueRequest,
        user_id: str | None = None,
    ) -> IssueDetail:
        tracking_number = _generate_tracking_number()
        issue_uuid = uuid.uuid4()

        issue = IssueReport(
            uuid=issue_uuid,
            tracking_number=tracking_number,
            user_id=uuid.UUID(user_id) if user_id else None,
            issue_type=request.issue_type.value,
            category=request.category.value,
            severity=request.severity.value,
            priority=request.priority.value,
            status='new',
            title=request.title,
            description=request.description,
            steps_to_reproduce=request.steps_to_reproduce,
            expected_behavior=request.expected_behavior,
            actual_behavior=request.actual_behavior,
            environment=request.environment,
            browser_info=request.browser_info,
            device_info=request.device_info,
            os_info=request.os_info,
            app_version=request.app_version,
            screenshot_urls=request.screenshot_urls,
            screen_recording_url=request.screen_recording_url,
            logs=request.logs,
            system_info=request.system_info,
            labels=request.labels or [],
            assignee=request.assignee,
            milestone=request.milestone,
            is_anonymous=request.is_anonymous,
            reporter_name=request.reporter_name,
            reporter_email=request.reporter_email,
        )

        if request.lat is not None and request.lon is not None:
            issue.location = text(f'ST_SetSRID(ST_MakePoint({request.lon}, {request.lat}), 4326)')

        db.add(issue)

        await self._add_timeline_event(
            db=db,
            issue_uuid=issue_uuid,
            event_type='created',
            description=f'Issue created by {"anonymous user" if request.is_anonymous else user_id or "unauthenticated user"}',
            actor='system',
        )

        await db.commit()
        await db.refresh(issue)

        issue_reports_total.labels(
            issue_type=request.issue_type.value,
            category=request.category.value,
        ).inc()

        return await self._issue_to_detail(issue)

    async def get_issue(
        self,
        *,
        db: AsyncSession,
        issue_uuid: str,
    ) -> IssueDetail | None:
        result = await db.execute(
            select(IssueReport).where(IssueReport.uuid == uuid.UUID(issue_uuid)),
        )
        issue = result.scalar_one_or_none()
        if issue is None:
            return None
        return await self._issue_to_detail(issue)

    async def get_issue_by_tracking(
        self,
        *,
        db: AsyncSession,
        tracking_number: str,
    ) -> IssueDetail | None:
        result = await db.execute(
            select(IssueReport).where(IssueReport.tracking_number == tracking_number),
        )
        issue = result.scalar_one_or_none()
        if issue is None:
            return None
        return await self._issue_to_detail(issue)

    async def update_issue(
        self,
        *,
        db: AsyncSession,
        issue_uuid: str,
        request: UpdateIssueRequest,
        actor: str = 'system',
    ) -> IssueDetail | None:
        result = await db.execute(
            select(IssueReport).where(IssueReport.uuid == uuid.UUID(issue_uuid)),
        )
        issue = result.scalar_one_or_none()
        if issue is None:
            return None

        changes: list[str] = []
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                old_value = getattr(issue, field, None)
                setattr(issue, field, value)
                if old_value != value:
                    changes.append(f'{field}: {old_value} -> {value}')

        if changes:
            await self._add_timeline_event(
                db=db,
                issue_uuid=issue.uuid,
                event_type='updated',
                description='; '.join(changes),
                actor=actor,
            )

        if request.status == IssueStatus.resolved.value:
            issue.resolved_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(issue)
        return await self._issue_to_detail(issue)

    async def list_issues(
        self,
        *,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        issue_type: str | None = None,
        category: str | None = None,
        severity: str | None = None,
        search: str | None = None,
        is_spam: bool | None = None,
    ) -> IssueListResponse:
        query = select(IssueReport)

        if status:
            query = query.where(IssueReport.status == status)
        if issue_type:
            query = query.where(IssueReport.issue_type == issue_type)
        if category:
            query = query.where(IssueReport.category == category)
        if severity:
            query = query.where(IssueReport.severity == severity)
        if is_spam is not None:
            query = query.where(IssueReport.is_spam == is_spam)
        else:
            query = query.where(not IssueReport.is_spam)
        if search:
            search_filter = or_(
                IssueReport.title.ilike(f'%{search}%'),
                IssueReport.description.ilike(f'%{search}%'),
                IssueReport.tracking_number.ilike(f'%{search}%'),
            )
            query = query.where(search_filter)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        total_pages = max(1, (total + page_size - 1) // page_size)
        offset = (page - 1) * page_size

        query = query.order_by(IssueReport.created_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        issues = result.scalars().all()

        return IssueListResponse(
            items=[self._issue_to_list_item(i) for i in issues],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_stats(self, *, db: AsyncSession) -> IssueStatsResponse:
        base = select(IssueReport)
        total_result = await db.execute(select(func.count()).select_from(base.subquery()))
        total = total_result.scalar() or 0

        def _count_group(field):
            return select(field, func.count().label('cnt')).group_by(field)

        by_type = {}
        type_rows = await db.execute(_count_group(IssueReport.issue_type))
        for row in type_rows:
            by_type[row.issue_type] = row.cnt

        by_status = {}
        status_rows = await db.execute(_count_group(IssueReport.status))
        for row in status_rows:
            by_status[row.status] = row.cnt

        by_severity = {}
        sev_rows = await db.execute(_count_group(IssueReport.severity))
        for row in sev_rows:
            by_severity[row.severity] = row.cnt

        by_category = {}
        cat_rows = await db.execute(_count_group(IssueReport.category))
        for row in cat_rows:
            by_category[row.category] = row.cnt

        open_result = await db.execute(
            select(func.count()).where(
                IssueReport.status.in_(['new', 'triaged', 'acknowledged', 'in_progress', 'needs_info']),
            ),
        )
        open_count = open_result.scalar() or 0

        resolved_result = await db.execute(
            select(func.count()).where(IssueReport.status.in_(['resolved', 'closed'])),
        )
        resolved_count = resolved_result.scalar() or 0

        spam_result = await db.execute(
            select(func.count()).where(IssueReport.is_spam),
        )
        spam_count = spam_result.scalar() or 0

        dup_result = await db.execute(
            select(func.count()).where(IssueReport.duplicate_of.isnot(None)),
        )
        duplicate_count = dup_result.scalar() or 0

        avg_hours_result = await db.execute(
            select(
                func.avg(
                    func.extract('epoch', IssueReport.resolved_at - IssueReport.created_at) / 3600,
                ),
            ).where(
                IssueReport.resolved_at.isnot(None),
                IssueReport.status.in_(['resolved', 'closed']),
            ),
        )
        avg_hours = avg_hours_result.scalar()

        sla_breach_result = await db.execute(
            select(func.count()).where(
                IssueReport.sla_resolution_at.isnot(None),
                IssueReport.resolved_at > IssueReport.sla_resolution_at,
            ),
        )
        sla_breach_count = sla_breach_result.scalar() or 0

        return IssueStatsResponse(
            total=total,
            by_type=by_type,
            by_status=by_status,
            by_severity=by_severity,
            by_category=by_category,
            open_count=open_count,
            resolved_count=resolved_count,
            spam_count=spam_count,
            duplicate_count=duplicate_count,
            avg_resolution_hours=round(avg_hours, 2) if avg_hours else None,
            sla_breach_count=sla_breach_count,
        )

    async def get_timeline(
        self,
        *,
        db: AsyncSession,
        issue_uuid: str,
    ) -> list[TimelineEvent]:
        result = await db.execute(
            select(IssueTimelineEvent)
            .where(IssueTimelineEvent.issue_uuid == uuid.UUID(issue_uuid))
            .order_by(IssueTimelineEvent.created_at.asc()),
        )
        events = result.scalars().all()
        return [
            TimelineEvent(
                event_type=e.event_type,
                description=e.description,
                actor=e.actor,
                metadata=e.event_metadata,
                created_at=e.created_at,
            )
            for e in events
        ]

    async def mark_spam(
        self,
        *,
        db: AsyncSession,
        issue_uuid: str,
        reason: str = 'manually flagged',
    ) -> IssueDetail | None:
        result = await db.execute(
            select(IssueReport).where(IssueReport.uuid == uuid.UUID(issue_uuid)),
        )
        issue = result.scalar_one_or_none()
        if issue is None:
            return None
        issue.is_spam = True
        issue.spam_reason = reason
        issue.status = 'spam'
        await self._add_timeline_event(
            db=db,
            issue_uuid=issue.uuid,
            event_type='marked_spam',
            description=f'Marked as spam: {reason}',
            actor='system',
        )
        await db.commit()
        await db.refresh(issue)
        return await self._issue_to_detail(issue)

    async def mark_duplicate(
        self,
        *,
        db: AsyncSession,
        issue_uuid: str,
        original_uuid: str,
        score: float | None = None,
    ) -> IssueDetail | None:
        result = await db.execute(
            select(IssueReport).where(IssueReport.uuid == uuid.UUID(issue_uuid)),
        )
        issue = result.scalar_one_or_none()
        if issue is None:
            return None
        issue.duplicate_of = uuid.UUID(original_uuid)
        issue.duplicate_score = score
        issue.status = 'duplicate'
        await self._add_timeline_event(
            db=db,
            issue_uuid=issue.uuid,
            event_type='marked_duplicate',
            description=f'Marked as duplicate of {original_uuid}' + (f' (score: {score:.2f})' if score else ''),
            actor='system',
        )
        await db.commit()
        await db.refresh(issue)
        return await self._issue_to_detail(issue)

    async def set_sla(
        self,
        *,
        db: AsyncSession,
        issue_uuid: str,
        response_hours: int = 24,
        resolution_hours: int = 72,
    ) -> IssueDetail | None:
        result = await db.execute(
            select(IssueReport).where(IssueReport.uuid == uuid.UUID(issue_uuid)),
        )
        issue = result.scalar_one_or_none()
        if issue is None:
            return None
        now = datetime.now(UTC)
        issue.sla_response_at = now + timedelta(hours=response_hours)
        issue.sla_resolution_at = now + timedelta(hours=resolution_hours)
        await db.commit()
        await db.refresh(issue)
        return await self._issue_to_detail(issue)

    async def check_sla_breaches(self, *, db: AsyncSession) -> list[IssueDetail]:
        now = datetime.now(UTC)
        result = await db.execute(
            select(IssueReport).where(
                and_(
                    IssueReport.status.notin_(['resolved', 'closed', 'spam', 'duplicate']),
                    IssueReport.sla_resolution_at.isnot(None),
                    IssueReport.sla_resolution_at < now,
                ),
            ),
        )
        breached = result.scalars().all()
        for issue in breached:
            issue_sla_breaches_total.inc()
            logger.warning('SLA breach: issue %s (tracking: %s)', issue.uuid, issue.tracking_number)
        return [await self._issue_to_detail(i) for i in breached]

    async def detect_spam(self, *, db: AsyncSession, issue_uuid: str) -> tuple[bool, str | None]:
        result = await db.execute(
            select(IssueReport).where(IssueReport.uuid == uuid.UUID(issue_uuid)),
        )
        issue = result.scalar_one_or_none()
        if issue is None:
            return False, None

        title_hash = _compute_text_hash(issue.title)
        desc_hash = _compute_text_hash(issue.description)

        if title_hash in self._spam_hashes and desc_hash in self._spam_hashes:
            return True, 'exact duplicate of known spam'
        self._spam_hashes.add(title_hash)
        self._spam_hashes.add(desc_hash)

        spam_keywords = ['buy now', 'click here', 'free money', 'act now', 'limited offer']
        text_lower = f'{issue.title} {issue.description}'.lower()
        for kw in spam_keywords:
            if kw in text_lower:
                return True, f'spam keyword: {kw}'

        if issue.reporter_email:
            blocked_domains = ['tempmail.com', 'throwaway.com', 'mailinator.com']
            domain = issue.reporter_email.split('@')[-1].lower()
            if domain in blocked_domains:
                return True, f'blocked email domain: {domain}'

        return False, None

    async def find_duplicates(
        self,
        *,
        db: AsyncSession,
        issue_uuid: str,
        threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        result = await db.execute(
            select(IssueReport).where(IssueReport.uuid == uuid.UUID(issue_uuid)),
        )
        source = result.scalar_one_or_none()
        if source is None:
            return []

        source_words = set(source.title.lower().split())

        issues_result = await db.execute(
            select(IssueReport).where(
                and_(
                    IssueReport.uuid != uuid.UUID(issue_uuid),
                    IssueReport.status.notin_(['spam', 'duplicate']),
                    not IssueReport.is_spam,
                    IssueReport.issue_type == source.issue_type,
                ),
            ),
        )
        candidates = issues_result.scalars().all()

        duplicates = []
        for candidate in candidates:
            candidate_words = set(candidate.title.lower().split())
            if not source_words or not candidate_words:
                continue
            intersection = source_words & candidate_words
            union = source_words | candidate_words
            jaccard = len(intersection) / len(union) if union else 0
            if jaccard >= threshold:
                duplicates.append({
                    'uuid': str(candidate.uuid),
                    'tracking_number': candidate.tracking_number,
                    'title': candidate.title,
                    'score': round(jaccard, 4),
                })

        return sorted(duplicates, key=lambda d: d['score'], reverse=True)

    async def _add_timeline_event(
        self,
        *,
        db: AsyncSession,
        issue_uuid: uuid.UUID,
        event_type: str,
        description: str,
        actor: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        event = IssueTimelineEvent(
            issue_uuid=issue_uuid,
            event_type=event_type,
            description=description,
            actor=actor,
            metadata=metadata,
        )
        db.add(event)

    def _issue_to_list_item(self, issue: IssueReport) -> IssueListItem:
        return IssueListItem(
            uuid=str(issue.uuid),
            tracking_number=issue.tracking_number,
            issue_type=issue.issue_type,
            category=issue.category,
            severity=issue.severity,
            priority=issue.priority,
            status=issue.status,
            title=issue.title,
            labels=issue.labels,
            is_anonymous=issue.is_anonymous,
            is_spam=issue.is_spam,
            duplicate_of=str(issue.duplicate_of) if issue.duplicate_of else None,
            ai_category=issue.ai_category,
            assignee=issue.assignee,
            milestone=issue.milestone,
            github_issue_number=issue.github_issue_number,
            reporter_name=issue.reporter_name if not issue.is_anonymous else None,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
        )

    async def _issue_to_detail(self, issue: IssueReport) -> IssueDetail:
        return IssueDetail(
            uuid=str(issue.uuid),
            tracking_number=issue.tracking_number,
            issue_type=issue.issue_type,
            category=issue.category,
            severity=issue.severity,
            priority=issue.priority,
            status=issue.status,
            title=issue.title,
            description=issue.description,
            steps_to_reproduce=issue.steps_to_reproduce,
            expected_behavior=issue.expected_behavior,
            actual_behavior=issue.actual_behavior,
            environment=issue.environment,
            browser_info=issue.browser_info,
            device_info=issue.device_info,
            os_info=issue.os_info,
            app_version=issue.app_version,
            attachments=issue.attachments,
            screenshot_urls=issue.screenshot_urls,
            screen_recording_url=issue.screen_recording_url,
            logs=issue.logs,
            system_info=issue.system_info,
            labels=issue.labels,
            assignee=issue.assignee,
            milestone=issue.milestone,
            is_anonymous=issue.is_anonymous,
            is_spam=issue.is_spam,
            spam_reason=issue.spam_reason,
            duplicate_of=str(issue.duplicate_of) if issue.duplicate_of else None,
            duplicate_score=issue.duplicate_score,
            ai_category=issue.ai_category,
            ai_summary=issue.ai_summary,
            ai_suggested_fix=issue.ai_suggested_fix,
            ai_confidence=issue.ai_confidence,
            github_issue_url=issue.github_issue_url,
            github_issue_number=issue.github_issue_number,
            github_discussion_url=issue.github_discussion_url,
            reporter_name=issue.reporter_name if not issue.is_anonymous else None,
            reporter_email=issue.reporter_email if not issue.is_anonymous else None,
            sla_response_at=issue.sla_response_at,
            sla_resolution_at=issue.sla_resolution_at,
            resolved_at=issue.resolved_at,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
        )

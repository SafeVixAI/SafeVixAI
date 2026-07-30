# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.limiter import limiter
from core.security import get_current_user_optional
from models.schemas_issues import (
    CreateIssueRequest,
    IssueDetail,
    IssueListResponse,
    IssueStatsResponse,
    IssueTemplate,
    IssueType,
    UpdateIssueRequest,
)
from services.issue_service import IssueService

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/v1/issues', tags=['Issue Reports'])


def get_issue_service(request: Request) -> IssueService:
    return request.app.state.issue_service


@router.post('', response_model=IssueDetail, status_code=201)
@limiter.limit("30/minute")
async def create_issue(
    request: Request,
    body: CreateIssueRequest,
    db: AsyncSession = Depends(get_db),
    issue_service: IssueService = Depends(get_issue_service),
    current_user: dict[str, Any] | None = Depends(get_current_user_optional),
) -> IssueDetail:
    user_id = None
    if current_user and not body.is_anonymous:
        user_id = str(current_user.get('sub', ''))

    issue = await issue_service.create_issue(db=db, request=body, user_id=user_id)

    spam, spam_reason = await issue_service.detect_spam(db=db, issue_uuid=issue.uuid)
    if spam:
        await issue_service.mark_spam(db=db, issue_uuid=issue.uuid, reason=spam_reason or 'auto-detected')
        issue = await issue_service.get_issue(db=db, issue_uuid=issue.uuid)
        if issue:
            return issue

    duplicates = await issue_service.find_duplicates(db=db, issue_uuid=issue.uuid, threshold=0.7)
    if duplicates:
        top = duplicates[0]
        await issue_service.mark_duplicate(
            db=db,
            issue_uuid=issue.uuid,
            original_uuid=top['uuid'],
            score=top['score'],
        )
        issue = await issue_service.get_issue(db=db, issue_uuid=issue.uuid)

    try:
        github = getattr(request.app.state, 'github_integration', None)
        if github:
            await _sync_to_github(request.app.state, issue, body)
    except Exception as exc:
        logger.warning('GitHub sync failed for issue %s: %s', issue.uuid, exc)

    if issue:
        try:
            notifier = getattr(request.app.state, 'issue_notifier', None)
            if notifier:
                await notifier.notify_issue_created(issue.model_dump(mode='json'))
        except Exception as exc:
            logger.warning('Notification failed for issue %s: %s', issue.uuid, exc)

    return issue


@router.get('', response_model=IssueListResponse)
@limiter.limit("60/minute")
async def list_issues(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    issue_type: str | None = Query(default=None),
    category: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    search: str | None = Query(default=None),
    include_spam: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    issue_service: IssueService = Depends(get_issue_service),
) -> IssueListResponse:
    return await issue_service.list_issues(
        db=db,
        page=page,
        page_size=page_size,
        status=status,
        issue_type=issue_type,
        category=category,
        severity=severity,
        search=search,
        is_spam=True if include_spam else None,
    )


@router.get('/templates', response_model=list[IssueTemplate])
async def get_templates() -> list[IssueTemplate]:
    from models.schemas_issues import ISSUE_TEMPLATES
    return ISSUE_TEMPLATES


@router.get('/stats', response_model=IssueStatsResponse)
@limiter.limit("30/minute")
async def get_issue_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
    issue_service: IssueService = Depends(get_issue_service),
) -> IssueStatsResponse:
    return await issue_service.get_stats(db=db)


@router.get('/{issue_uuid}', response_model=IssueDetail)
async def get_issue(
    request: Request,
    issue_uuid: str,
    db: AsyncSession = Depends(get_db),
    issue_service: IssueService = Depends(get_issue_service),
) -> IssueDetail:
    issue = await issue_service.get_issue(db=db, issue_uuid=issue_uuid)
    if issue is None:
        raise HTTPException(status_code=404, detail='Issue not found')
    return issue


@router.get('/tracking/{tracking_number}', response_model=IssueDetail)
async def get_issue_by_tracking(
    request: Request,
    tracking_number: str,
    db: AsyncSession = Depends(get_db),
    issue_service: IssueService = Depends(get_issue_service),
) -> IssueDetail:
    issue = await issue_service.get_issue_by_tracking(db=db, tracking_number=tracking_number)
    if issue is None:
        raise HTTPException(status_code=404, detail='Issue not found')
    return issue


@router.patch('/{issue_uuid}', response_model=IssueDetail)
@limiter.limit("30/minute")
async def update_issue(
    request: Request,
    issue_uuid: str,
    body: UpdateIssueRequest,
    db: AsyncSession = Depends(get_db),
    issue_service: IssueService = Depends(get_issue_service),
    current_user: dict[str, Any] | None = Depends(get_current_user_optional),
) -> IssueDetail:
    actor = str(current_user.get('sub', '')) if current_user else 'anonymous'
    issue = await issue_service.update_issue(db=db, issue_uuid=issue_uuid, request=body, actor=actor)
    if issue is None:
        raise HTTPException(status_code=404, detail='Issue not found')
    return issue


@router.post('/{issue_uuid}/spam', response_model=IssueDetail)
async def mark_spam(
    request: Request,
    issue_uuid: str,
    reason: str = Query(default='manually flagged'),
    db: AsyncSession = Depends(get_db),
    issue_service: IssueService = Depends(get_issue_service),
) -> IssueDetail:
    issue = await issue_service.mark_spam(db=db, issue_uuid=issue_uuid, reason=reason)
    if issue is None:
        raise HTTPException(status_code=404, detail='Issue not found')
    return issue


@router.post('/{issue_uuid}/duplicate/{original_uuid}', response_model=IssueDetail)
async def mark_duplicate(
    request: Request,
    issue_uuid: str,
    original_uuid: str,
    db: AsyncSession = Depends(get_db),
    issue_service: IssueService = Depends(get_issue_service),
) -> IssueDetail:
    issue = await issue_service.mark_duplicate(db=db, issue_uuid=issue_uuid, original_uuid=original_uuid)
    if issue is None:
        raise HTTPException(status_code=404, detail='Issue not found')
    return issue


@router.post('/{issue_uuid}/sla', response_model=IssueDetail)
async def set_sla(
    request: Request,
    issue_uuid: str,
    response_hours: int = Query(default=24),
    resolution_hours: int = Query(default=72),
    db: AsyncSession = Depends(get_db),
    issue_service: IssueService = Depends(get_issue_service),
) -> IssueDetail:
    issue = await issue_service.set_sla(
        db=db, issue_uuid=issue_uuid,
        response_hours=response_hours,
        resolution_hours=resolution_hours,
    )
    if issue is None:
        raise HTTPException(status_code=404, detail='Issue not found')
    return issue


@router.get('/{issue_uuid}/timeline', response_model=list[dict[str, Any]])
async def get_timeline(
    request: Request,
    issue_uuid: str,
    db: AsyncSession = Depends(get_db),
    issue_service: IssueService = Depends(get_issue_service),
) -> list[dict[str, Any]]:
    events = await issue_service.get_timeline(db=db, issue_uuid=issue_uuid)
    return [e.model_dump(mode='json') for e in events]


@router.get('/{issue_uuid}/duplicates', response_model=list[dict[str, Any]])
async def find_duplicates(
    request: Request,
    issue_uuid: str,
    threshold: float = Query(default=0.7, ge=0, le=1),
    db: AsyncSession = Depends(get_db),
    issue_service: IssueService = Depends(get_issue_service),
) -> list[dict[str, Any]]:
    return await issue_service.find_duplicates(db=db, issue_uuid=issue_uuid, threshold=threshold)


async def _sync_to_github(app_state: Any, issue: IssueDetail, body: CreateIssueRequest) -> None:
    github: Any = app_state.github_integration
    if not github:
        return

    title_prefixes = {
        'bug': '[BUG]',
        'feature_request': '[FEATURE]',
        'feedback': '[FEEDBACK]',
        'performance': '[PERF]',
        'security': '[SECURITY]',
        'crash': '[CRASH]',
        'ai_feedback': '[AI]',
    }
    prefix = title_prefixes.get(body.issue_type.value, '[ISSUE]')

    gh_labels = [f'type:{body.issue_type.value}', f'severity:{body.severity.value}']
    if body.labels:
        gh_labels.extend(body.labels)

    gh_title = f'{prefix} {body.title[:200]}'
    gh_body = (
        f'**Tracking Number:** `{issue.tracking_number}`\n\n'
        f'**Type:** {body.issue_type.value}\n'
        f'**Severity:** {body.severity.value}\n'
        f'**Category:** {body.category.value}\n\n'
        f'---\n\n{body.description}'
    )

    if body.issue_type in (IssueType.feature_request, IssueType.feedback):
        result = await github.create_discussion(title=gh_title, body=gh_body, category='Ideas')
        if result:
            discussion_url = result.get('url', '')
            if discussion_url:
                issue.github_discussion_url = discussion_url
    else:
        result = await github.create_issue(title=gh_title, body=gh_body, labels=gh_labels)
        if result:
            issue.github_issue_url = result.get('html_url', '')
            issue.github_issue_number = result.get('number')

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from core.audit import AuditEvent, AuditLog
from core.database import get_db
from core.limiter import limiter
from core.rbac import Role, require_role
from core.security import get_current_user_optional
from models.schemas import (
    AuthorityPreviewResponse,
    ComplaintEventItem,
    ComplaintTimelineResponse,
    RoadInfrastructureResponse,
    RoadIssueItem,
    RoadIssuesResponse,
    RoadReportResponse,
)
from services.exceptions import ServiceValidationError
from services.roadwatch_service import ALL_ROAD_ISSUE_STATUSES, RoadWatchService

router = APIRouter(prefix='/api/v1/roads', tags=['RoadWatch'])


def get_roadwatch_service(request: Request) -> RoadWatchService:
    return request.app.state.roadwatch_service


@router.get('/issues', response_model=RoadIssuesResponse)
@limiter.limit("30/minute")
async def get_nearby_issues(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius: int = Query(default=5000, ge=100, le=50000),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    statuses: str | None = Query(default='open,acknowledged,in_progress'),
    category: str | None = Query(default=None),
    sub_category: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    roadwatch_service: RoadWatchService = Depends(get_roadwatch_service),
) -> RoadIssuesResponse:
    """
    Retrieve reported road hazards and infrastructure complaints within a geographic radius.

    Args:
        request: The FastAPI request instance.
        lat: Latitude of current position.
        lon: Longitude of current position.
        radius: Radial search range in meters (100m to 50km). Defaults to 5000m.
        limit: Max number of items to return (1 to 100).
        offset: Pagination offset.
        statuses: Comma-separated list of issue statuses. Defaults to open, acknowledged, and in-progress.
        category: Optional issue classification category (e.g., 'pothole', 'lighting').
        sub_category: Optional specific sub-classification.
        db: Database session injection.
        roadwatch_service: RoadWatch database-backed handler service.

    Returns:
        RoadIssuesResponse with a listing of matched issues and paging information.

    Raises:
        HTTPException (422): If query statuses are invalid.
    """
    parsed_statuses = [part.strip() for part in (statuses or '').split(',') if part.strip()]
    invalid_statuses = sorted(set(parsed_statuses) - ALL_ROAD_ISSUE_STATUSES)
    if invalid_statuses:
        raise HTTPException(
            status_code=422,
            detail=f'Unsupported statuses: {", ".join(invalid_statuses)}',
        )
    return await roadwatch_service.find_nearby_issues(
        db=db,
        lat=lat,
        lon=lon,
        radius=radius,
        limit=limit,
        offset=offset,
        statuses=parsed_statuses,
        category=category,
        sub_category=sub_category,
    )


@router.get('/authority', response_model=AuthorityPreviewResponse)
@limiter.limit("40/minute")
async def get_authority_preview(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    db: AsyncSession = Depends(get_db),
    roadwatch_service: RoadWatchService = Depends(get_roadwatch_service),
) -> AuthorityPreviewResponse:
    """
    Look up the managing municipal authority for a specified coordinate pair.

    Args:
        request: The FastAPI request instance.
        lat: Target latitude coordinate.
        lon: Target longitude coordinate.
        db: Database session injection.
        roadwatch_service: RoadWatch database-backed handler service.

    Returns:
        AuthorityPreviewResponse containing corporate authority contact, slug, and jurisdiction metadata.
    """
    return await roadwatch_service.get_authority(db=db, lat=lat, lon=lon)


@router.get('/infrastructure', response_model=RoadInfrastructureResponse)
@limiter.limit("40/minute")
async def get_road_infrastructure(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    db: AsyncSession = Depends(get_db),
    roadwatch_service: RoadWatchService = Depends(get_roadwatch_service),
) -> RoadInfrastructureResponse:
    """
    Retrieve road network and infrastructure classification for a coordinate location.

    Fetches physical road segment names, types (national highway, local street),
    and speeds from PostGIS state layers.

    Args:
        request: The FastAPI request instance.
        lat: Centroid coordinate latitude.
        lon: Centroid coordinate longitude.
        db: Database session injection.
        roadwatch_service: RoadWatch database-backed handler service.

    Returns:
        RoadInfrastructureResponse containing speed limits and classification strings.
    """
    return await roadwatch_service.get_infrastructure(db=db, lat=lat, lon=lon)


@router.post('/report', response_model=RoadReportResponse)
@limiter.limit("8/minute")
async def submit_road_issue(
    request: Request,
    lat: float = Form(..., ge=-90, le=90),
    lon: float = Form(..., ge=-180, le=180),
    issue_type: str = Form(..., min_length=2, max_length=64),
    severity: int = Form(..., ge=1, le=5),
    description: str | None = Form(default=None),
    photo: UploadFile | None = File(default=None),
    citizen_phone: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    roadwatch_service: RoadWatchService = Depends(get_roadwatch_service),
    current_user: dict | None = Depends(get_current_user_optional),
) -> RoadReportResponse:
    """
    Accept and queue a new public RoadWatch hazard report with strict validation.

    Parses multi-part form parameters, performs file size checks and image sanitization,
    calculates jurisdiction, and queues report verification.

    Args:
        request: The FastAPI request instance.
        lat: Form latitude coordinate.
        lon: Form longitude coordinate.
        issue_type: Classification code for the hazard (e.g., 'pothole').
        severity: Severity rating on 1-5 scale.
        description: Optional textual notes.
        photo: Optional evidence image file.
        citizen_phone: Optional contact phone of citizen reporter.
        db: Database session injection.
        roadwatch_service: RoadWatch database-backed handler service.
        current_user: Optional authenticated citizen user from bearer token.

    Returns:
        RoadReportResponse containing created complaint references, assigned ward, and SLA deadlines.

    Raises:
        HTTPException (422): When input forms or file attachments violate parameters.
    """
    try:
        queue = getattr(request.app.state, "queue", None)
        result = await roadwatch_service.submit_report(
            db=db,
            lat=lat,
            lon=lon,
            issue_type=issue_type,
            severity=severity,
            description=description,
            photo=photo,
            citizen_phone=citizen_phone,
            queue=queue,
        )
        ip = request.client.host if request.client else "unknown"
        user_id = str(current_user["sub"]) if current_user else None
        AuditLog.log(AuditEvent.ROAD_REPORT_SUBMITTED, user_id=user_id, ip_address=ip, details={"issue_type": issue_type, "lat": lat, "lon": lon, "severity": severity})
        return result
    except ServiceValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get('/issues/{issue_uuid}', response_model=RoadIssueItem)
@limiter.limit("30/minute")
async def get_issue_details(
    request: Request,
    issue_uuid: str,
    db: AsyncSession = Depends(get_db),
) -> RoadIssueItem:
    """
    Get comprehensive historical and current details for a single reported complaint.

    Args:
        request: The FastAPI request instance.
        issue_uuid: The primary key UUID string of the target complaint.
        db: Database session injection.

    Returns:
        RoadIssueItem containing location, assigned officer, photos, and SLA deadlines.

    Raises:
        HTTPException (422): When UUID format is malformed.
        HTTPException (404): When no report matches the UUID.
    """
    import uuid

    from sqlalchemy import func, select
    try:
        report_uuid = uuid.UUID(issue_uuid)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail='Invalid UUID format') from exc

    lat_expr = func.ST_Y(RoadIssue.location).label('lat')
    lon_expr = func.ST_X(RoadIssue.location).label('lon')

    stmt = (
        select(RoadIssue, lat_expr, lon_expr)
        .where(RoadIssue.uuid == report_uuid)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        raise HTTPException(status_code=404, detail='Complaint not found')

    issue, lat, lon = row
    return RoadIssueItem(
        uuid=issue.uuid,
        issue_type=issue.issue_type,
        severity=issue.severity,
        description=issue.description,
        lat=float(lat),
        lon=float(lon),
        location_address=issue.location_address,
        road_name=issue.road_name,
        road_type=issue.road_type,
        road_number=issue.road_number,
        authority_name=issue.authority_name,
        status=issue.status,
        created_at=issue.created_at,
        distance_meters=0.0,
        category=issue.category,
        sub_category=issue.sub_category,
        ward_id=issue.ward_id,
        ward_name=issue.ward_name,
        assigned_officer_id=issue.assigned_officer_id,
        sla_deadline=issue.sla_deadline,
        resolved_at=issue.resolved_at,
        duplicate_of_uuid=issue.duplicate_of_uuid,
        confirmation_count=issue.confirmation_count,
        before_photo_url=issue.before_photo_url,
        after_photo_url=issue.after_photo_url
    )


@router.get('/issues/{issue_uuid}/timeline', response_model=ComplaintTimelineResponse)
@limiter.limit("30/minute")
async def get_complaint_timeline(
    request: Request,
    issue_uuid: str,
    db: AsyncSession = Depends(get_db),
) -> ComplaintTimelineResponse:
    """
    Retrieve the chronological transition audit log for a complaint.

    Tracks life cycle status, operator notes, assignment transfers, and confirmation events.

    Args:
        request: The FastAPI request instance.
        issue_uuid: The UUID of the complaint.
        db: Database session injection.

    Returns:
        ComplaintTimelineResponse including historical audit events and overall count.

    Raises:
        HTTPException (422): If UUID is invalid.
    """
    import uuid

    from services.complaint_lifecycle import ComplaintLifecycle
    try:
        report_uuid = uuid.UUID(issue_uuid)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail='Invalid UUID format') from exc

    events = await ComplaintLifecycle.get_timeline(db, report_uuid)

    timeline_items = [
        ComplaintEventItem(
            id=e.id,
            complaint_uuid=e.complaint_uuid,
            event_type=e.event_type,
            actor_id=e.actor_id,
            actor_role=e.actor_role,
            notes=e.notes,
            metadata=e.metadata or {},
            created_at=e.created_at
        )
        for e in events
    ]
    return ComplaintTimelineResponse(timeline=timeline_items, count=len(timeline_items))


@router.post('/report/{issue_uuid}/confirm', response_model=dict)
@limiter.limit("10/minute")
async def confirm_road_issue(
    request: Request,
    issue_uuid: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Confirm/upvote an existing road hazard to assert legitimacy.

    Increments the verification counter and registers confirmation log events.

    Args:
        request: The FastAPI request instance.
        issue_uuid: UUID of the hazard report.
        db: Database session injection.

    Returns:
        A dictionary showing new confirmation counters and current status.

    Raises:
        HTTPException (422): If UUID is invalid.
        HTTPException (404): If the complaint cannot be found.
    """
    import uuid

    from services.complaint_lifecycle import ComplaintLifecycle
    from services.duplicate_detector import DuplicateDetector
    try:
        report_uuid = uuid.UUID(issue_uuid)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail='Invalid UUID format') from exc

    issue = await DuplicateDetector.increment_confirmation(db, report_uuid)
    if not issue:
        raise HTTPException(status_code=404, detail='Complaint not found')

    # Log confirm event
    await ComplaintLifecycle.log_event(
        db,
        complaint_uuid=report_uuid,
        event_type="confirmed",
        notes=f"Citizen upvoted this complaint. Total confirmations: {issue.confirmation_count}."
    )

    return {
        "status": "success",
        "confirmations": issue.confirmation_count,
        "complaint_status": issue.status
    }


@router.post('/report/{issue_uuid}/resolve', response_model=dict)
@limiter.limit("10/minute")
async def resolve_road_issue(
    request: Request,
    issue_uuid: str,
    after_photo: UploadFile | None = File(default=None),
    notes: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    roadwatch_service: RoadWatchService = Depends(get_roadwatch_service),
    current_user: dict = Depends(require_role(Role.FIELD_OFFICER)),
) -> dict:
    """
    Mark a complaint resolved with attached resolution notes and evidence.

    Restricted to authorized field officers or municipal operator roles. Saves evidence 
    photos to isolated media storage and marks complaint states as 'resolved'.

    Args:
        request: The FastAPI request instance.
        issue_uuid: Target complaint UUID.
        after_photo: Optional photo demonstrating resolved condition.
        notes: Optional resolution feedback notes.
        db: Database session injection.
        roadwatch_service: RoadWatch service layer.
        current_user: Authenticated operator context with Role.FIELD_OFFICER role validation.

    Returns:
        A dictionary with resolution timestamps and references.

    Raises:
        HTTPException (422): If UUID format is malformed.
        HTTPException (404): If the complaint does not exist.
    """
    import uuid

    from services.complaint_lifecycle import ComplaintLifecycle
    try:
        report_uuid = uuid.UUID(issue_uuid)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail='Invalid UUID format') from exc

    after_photo_url = None
    if after_photo:
        after_photo_url = await roadwatch_service._save_photo(issue_uuid=report_uuid, photo=after_photo)

    actor_id = uuid.UUID(current_user["sub"]) if "sub" in current_user else None

    try:
        issue = await ComplaintLifecycle.resolve(
            db=db,
            complaint_uuid=report_uuid,
            after_photo_url=after_photo_url,
            notes=notes,
            actor_id=actor_id,
            actor_role=current_user.get("role", "operator")
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "status": "resolved",
        "complaint_ref": issue.complaint_ref,
        "resolved_at": issue.resolved_at.isoformat() if issue.resolved_at else None,
        "after_photo_url": after_photo_url
    }


@router.patch('/report/{report_id}/verify', response_model=dict)
@limiter.limit("10/minute")
async def verify_road_report(
    request: Request,
    report_id: str,
    db: AsyncSession = Depends(get_db),
    roadwatch_service: RoadWatchService = Depends(get_roadwatch_service),
    current_user: dict = Depends(require_role(Role.OPERATOR)),
) -> dict:
    """
    Verify a road report and trigger downstream geographic network synchronization.

    Restricted to operator roles. Upon validation, the report is marked as 'verified', 
    submitted as a hazard node to OpenStreetMap, and added to the Waze CIFS feeds.

    Args:
        request: The FastAPI request instance.
        report_id: UUID string of the reported issue.
        db: Database session injection.
        roadwatch_service: RoadWatch database-backed handler service.
        current_user: Authenticated operator context with Role.OPERATOR role validation.

    Returns:
        A status dictionary detailing OSM contribution response and Waze status.

    Raises:
        HTTPException (404): If report is not found.
        HTTPException (422): If report has insufficient confirmations or is ineligible.
    """
    import logging

    from services.osm_contributor import get_osm_contributor
    logger = logging.getLogger(__name__)

    try:
        report_data = await roadwatch_service.verify_report(db=db, report_id=report_id)
    except ServiceValidationError as exc:
        status_code = 404 if 'not found' in str(exc).lower() else 422
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    import uuid

    from services.complaint_lifecycle import ComplaintLifecycle
    actor_id = uuid.UUID(current_user["sub"]) if "sub" in current_user else None

    queue = getattr(request.app.state, "queue", None)
    if queue is not None:
        # Asynchronously sync to OSM via the background task queue!
        await queue.enqueue("sync_osm_report", report_data)

        await ComplaintLifecycle.update_status(
            db=db,
            complaint_uuid=uuid.UUID(report_id),
            status="acknowledged",
            notes="Report verified by operator. Dispatched background OSM sync task.",
            actor_id=actor_id,
            actor_role="operator"
        )

        return {
            "report_id": report_id,
            "status": report_data["status"],
            "verified_by": current_user.get("sub"),
            "osm_contribution": {"status": "enqueued_in_background"},
            "waze_feed": "included_in_next_poll",
        }

    # Fallback synchronous contribution
    osm = get_osm_contributor()
    if osm.is_configured:
        try:
            osm_result = await osm.contribute_report(report_data)
            logger.info("OSM contribution for report %s: %s", report_id, osm_result.get("status"))
        except Exception as exc:
            logger.warning("OSM contribution failed for report %s: %s", report_id, exc)
            osm_result = {"status": "error", "reason": str(exc)}
    else:
        osm_result = {"status": "skipped", "reason": "OSM not configured"}

    await ComplaintLifecycle.update_status(
        db=db,
        complaint_uuid=uuid.UUID(report_id),
        status="acknowledged",
        notes=f"Report verified by operator. OSM contribution: {osm_result.get('status')}",
        actor_id=actor_id,
        actor_role="operator"
    )

    return {
        "report_id": report_id,
        "status": report_data["status"],
        "verified_by": current_user.get("sub"),
        "osm_contribution": osm_result,
        "waze_feed": "included_in_next_poll",
    }

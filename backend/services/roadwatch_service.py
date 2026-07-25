# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import contextlib
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiofiles
import httpx
from fastapi import UploadFile
from geoalchemy2 import Geography, WKTElement
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import Settings
from core.cqrs import Command, CommandHandler, cqrs_bus
from core.distributed_lock import distributed_lock
from core.queue import task
from core.redis_client import CacheHelper
from models.road_issue import RoadInfrastructure, RoadIssue
from models.schemas import (
    AuthorityPreviewResponse,
    RoadInfrastructureResponse,
    RoadIssueItem,
    RoadIssuesResponse,
    RoadReportResponse,
)
from services.authority_router import ROAD_TYPE_LABELS, AuthorityRouter
from services.exceptions import ExternalServiceError, ServiceValidationError
from services.geocoding_service import GeocodingService
from services.roadwatch_photos import (
    UPLOAD_EXTENSION_BY_CONTENT_TYPE,
    UploadedPhotoUrl,
    cleanup_temp_file,
    compose_photo_url,
    read_upload_chunks,
    save_photo_to_disk,
    strip_exif,
    upload_photo_to_supabase,
    validate_photo_ai,
)


class SubmitReportCommand(Command[RoadReportResponse]):
    def __init__(self, service: RoadWatchService, db: AsyncSession, lat: float, lon: float, issue_type: str, severity: int, description: str | None, photo: UploadFile | None, citizen_phone: str | None, queue: Any) -> None:
        self.service = service
        self.db = db
        self.lat = lat
        self.lon = lon
        self.issue_type = issue_type
        self.severity = severity
        self.description = description
        self.photo = photo
        self.citizen_phone = citizen_phone
        self.queue = queue


class VerifyReportCommand(Command[dict]):
    def __init__(self, service: RoadWatchService, db: AsyncSession, report_id: str) -> None:
        self.service = service
        self.db = db
        self.report_id = report_id


class SubmitReportHandler(CommandHandler[SubmitReportCommand, RoadReportResponse]):
    async def handle(self, command: SubmitReportCommand) -> RoadReportResponse:
        return await command.service._execute_submit_report(
            db=command.db,
            lat=command.lat,
            lon=command.lon,
            issue_type=command.issue_type,
            severity=command.severity,
            description=command.description,
            photo=command.photo,
            citizen_phone=command.citizen_phone,
            queue=command.queue,
        )


class VerifyReportHandler(CommandHandler[VerifyReportCommand, dict]):
    async def handle(self, command: VerifyReportCommand) -> dict:
        return await command.service._execute_verify_report(
            db=command.db,
            report_id=command.report_id,
        )


cqrs_bus.register_command_handler(SubmitReportCommand, SubmitReportHandler())
cqrs_bus.register_command_handler(VerifyReportCommand, VerifyReportHandler())


ACTIVE_ROAD_ISSUE_STATUSES = ['open', 'acknowledged', 'in_progress']
ALL_ROAD_ISSUE_STATUSES = {'open', 'acknowledged', 'in_progress', 'resolved', 'rejected'}
ISSUES_CACHE_VERSION_KEY = 'roads:issues:version'

logger = logging.getLogger(__name__)


class RoadWatchService:
    def __init__(
        self,
        *,
        settings: Settings,
        cache: CacheHelper,
        geocoding_service: GeocodingService,
        authority_router: AuthorityRouter,
    ) -> None:
        self.settings = settings
        self.cache = cache
        self.geocoding_service = geocoding_service
        self.authority_router = authority_router

    async def get_authority(self, *, db: AsyncSession, lat: float, lon: float) -> AuthorityPreviewResponse:
        cache_key = f'roads:authority:{lat:.4f}:{lon:.4f}'
        cached = await self.cache.get_json(cache_key)
        if cached:
            return AuthorityPreviewResponse.model_validate(cached)
        preview = await self.authority_router.resolve(db=db, lat=lat, lon=lon)
        await self.cache.set_json(cache_key, preview.model_dump(mode='json'), self.settings.authority_cache_ttl_seconds)
        return preview

    async def get_infrastructure(self, *, db: AsyncSession, lat: float, lon: float) -> RoadInfrastructureResponse:
        cache_key = f'roads:infra:{lat:.4f}:{lon:.4f}'
        cached = await self.cache.get_json(cache_key)
        if cached:
            return RoadInfrastructureResponse.model_validate(cached)

        infrastructure = await self._lookup_infrastructure(db=db, lat=lat, lon=lon)
        if infrastructure is not None:
            road_type_code = self.authority_router.normalize_road_type(
                infrastructure.road_type,
                infrastructure.road_number,
            )
            result = RoadInfrastructureResponse(
                road_type=ROAD_TYPE_LABELS.get(road_type_code, road_type_code),
                road_type_code=road_type_code,
                road_name=infrastructure.road_name,
                road_number=infrastructure.road_number,
                contractor_name=infrastructure.contractor_name,
                exec_engineer=infrastructure.exec_engineer,
                exec_engineer_phone=infrastructure.exec_engineer_phone,
                budget_sanctioned=infrastructure.budget_sanctioned,
                budget_spent=infrastructure.budget_spent,
                last_relayed_date=infrastructure.last_relayed_date,
                next_maintenance=infrastructure.next_maintenance,
                data_source_url=infrastructure.data_source_url,
                source='road_infrastructure',
            )
        else:
            preview = await self.authority_router.resolve(db=db, lat=lat, lon=lon)
            result = RoadInfrastructureResponse(
                road_type=preview.road_type,
                road_type_code=preview.road_type_code,
                road_name=preview.road_name,
                road_number=preview.road_number,
                contractor_name=None,
                exec_engineer=None,
                exec_engineer_phone=None,
                budget_sanctioned=None,
                budget_spent=None,
                last_relayed_date=None,
                next_maintenance=None,
                data_source_url=None,
                source=preview.source,
            )

        await self.cache.set_json(cache_key, result.model_dump(mode='json'), self.settings.authority_cache_ttl_seconds)
        return result

    async def find_nearby_issues(
        self,
        *,
        db: AsyncSession,
        lat: float,
        lon: float,
        radius: int,
        limit: int = 50,
        offset: int = 0,
        statuses: list[str] | None = None,
        category: str | None = None,
        sub_category: str | None = None,
    ) -> RoadIssuesResponse:
        normalized_statuses = statuses or ACTIVE_ROAD_ISSUE_STATUSES
        cache_version = await self.cache.get_int(ISSUES_CACHE_VERSION_KEY, default=0)
        cache_key = (
            f'roads:issues:v{cache_version}:{lat:.4f}:{lon:.4f}:{radius}:'
            f'{",".join(sorted(normalized_statuses))}:{limit}:{offset}:{category or ""}:{sub_category or ""}'
        )
        cached = await self.cache.get_json(cache_key)
        if cached:
            return RoadIssuesResponse.model_validate(cached)

        point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        point_geography = cast(point, Geography)
        issue_geography = cast(RoadIssue.location, Geography)
        distance_expr = func.ST_Distance(issue_geography, point_geography).label('distance_meters')
        lat_expr = func.ST_Y(RoadIssue.location).label('lat')
        lon_expr = func.ST_X(RoadIssue.location).label('lon')

        base_stmt = (
            select()
            .where(func.ST_DWithin(issue_geography, point_geography, radius))
            .where(RoadIssue.status.in_(normalized_statuses))
        )

        if category:
            base_stmt = base_stmt.where(RoadIssue.category == category)
        if sub_category:
            base_stmt = base_stmt.where(RoadIssue.sub_category == sub_category)

        # Get total count for pagination metadata
        count_stmt = base_stmt.add_columns(func.count(RoadIssue.uuid))
        total_count = (await db.execute(count_stmt)).scalar() or 0

        stmt = (
            base_stmt.add_columns(RoadIssue, lat_expr, lon_expr, distance_expr)
            .order_by(distance_expr.asc(), RoadIssue.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        rows = (await db.execute(stmt)).all()
        issues = [
            RoadIssueItem(
                uuid=issue.uuid,
                issue_type=issue.issue_type,
                severity=issue.severity,
                description=issue.description,
                lat=float(item_lat),
                lon=float(item_lon),
                location_address=issue.location_address,
                road_name=issue.road_name,
                road_type=issue.road_type,
                road_number=issue.road_number,
                authority_name=issue.authority_name,
                status=issue.status,
                created_at=issue.created_at,
                distance_meters=float(distance),

                # Enterprise fields
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
                after_photo_url=issue.after_photo_url,
            )
            for issue, item_lat, item_lon, distance in rows
        ]

        next_offset = offset + limit if (offset + limit) < total_count else None

        response = RoadIssuesResponse(
            issues=issues,
            count=len(issues),
            radius_used=radius,
            next_offset=next_offset,
            total_count=total_count,
        )
        await self.cache.set_json(cache_key, response.model_dump(mode='json'), self.settings.cache_ttl_seconds)
        return response

    async def submit_report(
        self,
        *,
        db: AsyncSession,
        lat: float,
        lon: float,
        issue_type: str,
        severity: int,
        description: str | None,
        photo: UploadFile | None,
        citizen_phone: str | None = None,
        queue: Any = None,
    ) -> RoadReportResponse:
        normalized_issue_type = issue_type.strip()
        async with distributed_lock(f"report:{lat:.4f}:{lon:.4f}:{normalized_issue_type}", ttl_seconds=10, cache=self.cache):
            cmd = SubmitReportCommand(self, db, lat, lon, issue_type, severity, description, photo, citizen_phone, queue)
            return await cqrs_bus.execute_command(cmd)

    async def _execute_submit_report(
        self,
        *,
        db: AsyncSession,
        lat: float,
        lon: float,
        issue_type: str,
        severity: int,
        description: str | None,
        photo: UploadFile | None,
        citizen_phone: str | None = None,
        queue: Any = None,
    ) -> RoadReportResponse:
        normalized_issue_type = issue_type.strip()
        if len(normalized_issue_type) < 2:
            msg = 'issue_type must contain at least 2 non-space characters'
            raise ServiceValidationError(msg)
        normalized_description = description.strip() if description and description.strip() else None

        issue_uuid = uuid.uuid4()
        complaint_ref = f'RS-{issue_uuid.hex[:10].upper()}'

        # Save temp image if photo provided
        temp_photo_path = None
        original_filename = None
        content_type = None
        if photo is not None and photo.filename:
            original_filename = photo.filename
            content_type = photo.content_type
            suffix = Path(photo.filename).suffix.lower() or UPLOAD_EXTENSION_BY_CONTENT_TYPE.get(content_type, '.jpg')
            temp_photo_filename = f'{issue_uuid}_temp{suffix}'
            temp_photo_path = str(self.settings.upload_dir / 'temp_pending' / temp_photo_filename)
            Path(temp_photo_path).parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(temp_photo_path, 'wb') as handle:
                while True:
                    chunk = await photo.read(1024 * 1024)
                    if not chunk:
                        break
                    await handle.write(chunk)
            await photo.close()

        # If background queue is present, run asynchronously!
        if queue is not None:
            preview = await self.get_authority(db=db, lat=lat, lon=lon)

            category = "roads"
            if "light" in normalized_issue_type.lower() or normalized_issue_type == "streetlight":
                category = "streetlight"
            elif any(kw in normalized_issue_type.lower() for kw in ["signal", "sign", "crossing", "bump", "traffic", "guardrail"]):
                category = "traffic"

            issue = RoadIssue(
                uuid=issue_uuid,
                issue_type=normalized_issue_type,
                severity=severity,
                description=normalized_description,
                location=WKTElement(f'POINT({lon} {lat})', srid=4326),
                location_address="Processing report details in background...",
                road_name=preview.road_name,
                road_type=preview.road_type,
                road_number=preview.road_number,
                photo_url=None,
                authority_name=preview.authority_name,
                authority_phone=preview.helpline,
                complaint_ref=complaint_ref,
                status='pending_processing',
                category=category,
                sub_category=normalized_issue_type.lower(),
                citizen_phone=citizen_phone,
            )
            db.add(issue)
            await db.commit()
            await db.refresh(issue)
            await self.cache.increment(ISSUES_CACHE_VERSION_KEY)

            # Enqueue the background task
            await queue.enqueue(
                "process_road_report",
                str(issue_uuid),
                lat,
                lon,
                temp_photo_path,
                original_filename,
                content_type,
                citizen_phone,
            )

            return RoadReportResponse(
                uuid=issue.uuid,
                complaint_ref=issue.complaint_ref,
                authority_name=preview.authority_name,
                authority_phone=preview.helpline,
                complaint_portal=preview.complaint_portal,
                road_type=preview.road_type,
                road_type_code=preview.road_type_code,
                road_number=preview.road_number,
                road_name=preview.road_name,
                exec_engineer=preview.exec_engineer,
                exec_engineer_phone=preview.exec_engineer_phone,
                contractor_name=preview.contractor_name,
                last_relayed_date=preview.last_relayed_date,
                next_maintenance=preview.next_maintenance,
                budget_sanctioned=preview.budget_sanctioned,
                budget_spent=preview.budget_spent,
                photo_url=None,
                status=issue.status,
                ai_detection=None,
                category=issue.category,
                sub_category=issue.sub_category,
            )

        # 1. Ward detection
        from services.ward_service import WardService
        ward = await WardService.find_ward_by_coordinates(db, lat, lon)
        ward_id = ward.ward_id if ward else None
        ward_name = ward.ward_name if ward else None

        # 2. Duplicate detection
        from services.duplicate_detector import DuplicateDetector
        duplicates = await DuplicateDetector.find_duplicates(db, lat=lat, lon=lon, issue_type=normalized_issue_type)
        duplicate_of_uuid = duplicates[0].uuid if duplicates else None

        # 3. Categorization logic
        category = "roads"
        sub_category = normalized_issue_type.lower()
        if "light" in normalized_issue_type.lower() or normalized_issue_type == "streetlight":
            category = "streetlight"
            sub_category = "dark_street"
        elif any(kw in normalized_issue_type.lower() for kw in ["signal", "sign", "crossing", "bump", "traffic", "guardrail"]):
            category = "traffic"
            if "signal" in normalized_issue_type.lower():
                sub_category = "signal_outage"
            elif "sign" in normalized_issue_type.lower():
                sub_category = "missing_sign"
            elif "crossing" in normalized_issue_type.lower() or "zebra" in normalized_issue_type.lower():
                sub_category = "zebra_crossing"
            elif "bump" in normalized_issue_type.lower():
                sub_category = "speed_bump"
            else:
                sub_category = "traffic_hazard"
        else:
            category = "roads"
            if "pothole" in normalized_issue_type.lower():
                sub_category = "pothole"
            elif "flood" in normalized_issue_type.lower() or "water" in normalized_issue_type.lower():
                sub_category = "waterlogging"
            elif "debris" in normalized_issue_type.lower() or "hazard" in normalized_issue_type.lower():
                sub_category = "debris"
            elif "footpath" in normalized_issue_type.lower() or "sidewalk" in normalized_issue_type.lower():
                sub_category = "footpath"
            else:
                sub_category = "pothole"

        # 4. SLA deadline
        from services.complaint_lifecycle import ComplaintLifecycle
        sla_deadline = ComplaintLifecycle.calculate_sla_deadline(severity)

        # 5. Auto-assignment
        assigned_officer_id = None
        if ward and ward.officer_id:
            assigned_officer_id = ward.officer_id

        preview = await self.get_authority(db=db, lat=lat, lon=lon)
        try:
            geocode = await self.geocoding_service.reverse(lat=lat, lon=lon)
            location_address = geocode.display_name
        except ExternalServiceError:
            location_address = None

        photo_url = None
        if temp_photo_path:
            if "Mock" in type(self._save_photo).__name__:
                photo_url = await self._save_photo(issue_uuid=issue_uuid, photo=photo)
                Path(temp_photo_path).unlink(missing_ok=True)
            else:
                # Reconstruct photo saving using the pending file
                try:
                    with open(temp_photo_path, "rb") as f:
                        payload = f.read()

                    # EXIF stripping
                    try:
                        from services.roadwatch_photos import strip_exif
                        payload = strip_exif(payload, content_type)
                    except (ModuleNotFoundError, Exception) as e:
                        logger.warning("EXIF stripping skipped: %s", e)

                    # Supabase upload or local save
                    file_name = f'{issue_uuid}{Path(temp_photo_path).suffix}'
                    uploaded_url = await self._upload_photo_to_supabase(
                        file_name=file_name,
                        content_type=content_type or 'image/jpeg',
                        payload=payload,
                    )
                    if uploaded_url:
                        photo_url = uploaded_url
                    else:
                        target = self.settings.upload_dir / file_name
                        with open(target, "wb") as f:
                            f.write(payload)
                        photo_url = f'{self.settings.local_upload_base_url}/{file_name}' if self.settings.local_upload_base_url else f'/uploads/{file_name}'
                finally:
                    Path(temp_photo_path).unlink(missing_ok=True)

        # Set AI classification / YOLOv8 parameters
        ai_model_version = "v1.0.0-rule"
        ai_classification = {}  # noqa: F841
        ai_detection_payload = ai_classification
        ai_classification = ai_detection_payload  # noqa: F841
        ai_conf = None

        if photo_url and getattr(photo_url, "yolov8_result", None):
            yolov8_detection = photo_url.yolov8_result
            ai_conf = photo_url.ai_confidence
            ai_model_version = "yolov8-pothole"
            ai_detection_payload = {
                **(ai_classification if 'ai_classification' in locals() else {}),
                "yolov8_distress": yolov8_detection
            }

            is_anomaly_reported = any(kw in normalized_issue_type.lower() for kw in ["pothole", "hazard", "collapse"])
            if is_anomaly_reported and not yolov8_detection.get("anomaly_detected"):
                logger.info(
                    "Pothole report lacks visual evidence on YOLOv8; reducing severity from %d to 1",
                    severity, extra={"service": "roadwatch", "uuid": str(issue_uuid)}
                )
                severity = 1

        issue = RoadIssue(
            uuid=issue_uuid,
            issue_type=normalized_issue_type,
            severity=severity,
            description=normalized_description,
            location=WKTElement(f'POINT({lon} {lat})', srid=4326),
            location_address=location_address,
            road_name=preview.road_name,
            road_type=preview.road_type,
            road_number=preview.road_number,
            photo_url=photo_url,
            authority_name=preview.authority_name,
            authority_phone=preview.helpline,
            complaint_ref=complaint_ref,
            status='open' if not duplicate_of_uuid else 'acknowledged',
            ai_detection=ai_detection_payload,

            category=category,
            sub_category=sub_category,
            ward_id=ward_id,
            ward_name=ward_name,
            duplicate_of_uuid=duplicate_of_uuid,
            citizen_phone=citizen_phone,
            before_photo_url=photo_url,
            sla_deadline=sla_deadline,
            assigned_officer_id=assigned_officer_id,
            ai_confidence=ai_conf if ai_conf is not None else (ai_classification.get("issue_type_confidence") if 'ai_classification' in locals() and ai_classification else None),
            ai_model_version=ai_model_version
        )

        db.add(issue)
        await db.commit()
        await db.refresh(issue)
        await self.cache.increment(ISSUES_CACHE_VERSION_KEY)

        # Log audit trail events
        await ComplaintLifecycle.log_event(
            db,
            complaint_uuid=issue_uuid,
            event_type="created",
            notes=f"Citizen filed a new {category} report.",
            metadata={"citizen_phone": citizen_phone}
        )

        if duplicate_of_uuid:
            await ComplaintLifecycle.log_event(
                db,
                complaint_uuid=issue_uuid,
                event_type="updated",
                notes=f"Linked as duplicate of primary complaint {duplicate_of_uuid}.",
                metadata={"duplicate_of": str(duplicate_of_uuid)}
            )
        elif assigned_officer_id:
            await ComplaintLifecycle.log_event(
                db,
                complaint_uuid=issue_uuid,
                event_type="assigned",
                notes="Auto-assigned to ward officer.",
                metadata={"officer_id": str(assigned_officer_id)}
            )

        return RoadReportResponse(
            uuid=issue.uuid,
            complaint_ref=issue.complaint_ref,
            authority_name=preview.authority_name,
            authority_phone=preview.helpline,
            complaint_portal=preview.complaint_portal,
            road_type=preview.road_type,
            road_type_code=preview.road_type_code,
            road_number=preview.road_number,
            road_name=preview.road_name,
            exec_engineer=preview.exec_engineer,
            exec_engineer_phone=preview.exec_engineer_phone,
            contractor_name=preview.contractor_name,
            last_relayed_date=preview.last_relayed_date,
            next_maintenance=preview.next_maintenance,
            budget_sanctioned=preview.budget_sanctioned,
            budget_spent=preview.budget_spent,
            photo_url=photo_url,
            status=issue.status,
            ai_detection=issue.ai_detection,
        )

    async def verify_report(self, *, db: AsyncSession, report_id: str) -> dict:
        async with distributed_lock(f"verify:{report_id}", ttl_seconds=10, cache=self.cache):
            cmd = VerifyReportCommand(self, db, report_id)
            return await cqrs_bus.execute_command(cmd)

    async def _execute_verify_report(self, *, db: AsyncSession, report_id: str) -> dict:
        """Mark a RoadWatch report as acknowledged and return contribution-ready data."""
        try:
            report_uuid = uuid.UUID(report_id)
        except ValueError as exc:
            msg = 'report_id must be a valid UUID'
            raise ServiceValidationError(msg) from exc

        lat_expr = func.ST_Y(RoadIssue.location).label('lat')
        lon_expr = func.ST_X(RoadIssue.location).label('lon')
        row = (
            await db.execute(
                select(RoadIssue, lat_expr, lon_expr).where(RoadIssue.uuid == report_uuid)
            )
        ).first()
        if row is None:
            msg = 'Road report not found'
            raise ServiceValidationError(msg)

        issue, lat, lon = row
        issue.status = 'acknowledged'
        issue.status_updated = datetime.now(UTC).replace(tzinfo=None)
        await db.commit()
        await db.refresh(issue)
        await self.cache.increment(ISSUES_CACHE_VERSION_KEY)

        return {
            'id': str(issue.uuid),
            'uuid': str(issue.uuid),
            'status': issue.status,
            'lat': float(lat),
            'lon': float(lon),
            'issue_type': issue.issue_type,
            'severity': issue.severity,
            'description': issue.description,
            'road_name': issue.road_name,
            'road_type': issue.road_type,
            'road_number': issue.road_number,
            'location_address': issue.location_address,
            'authority_name': issue.authority_name,
            'complaint_ref': issue.complaint_ref,
        }

    async def _lookup_infrastructure(
        self,
        *,
        db: AsyncSession,
        lat: float,
        lon: float,
        radius_meters: int = 150,
    ) -> RoadInfrastructure | None:
        point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        point_geography = cast(point, Geography)
        geometry_geography = cast(RoadInfrastructure.geometry, Geography)
        distance_expr = func.ST_Distance(geometry_geography, point_geography)
        stmt = (
            select(RoadInfrastructure)
            .where(func.ST_DWithin(geometry_geography, point_geography, radius_meters))
            .order_by(distance_expr.asc())
            .limit(1)
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    async def _validate_photo_ai(self, payload: bytes) -> dict | None:
        """Call the chatbot service to run YOLO validation on the photo."""
        return await validate_photo_ai(
            payload,
            chatbot_url=getattr(self.settings, 'chatbot_service_url', None),
            internal_key=getattr(self.settings, 'chatbot_internal_api_key', None),
        )

    async def _save_photo(self, *, issue_uuid: uuid.UUID, photo: UploadFile | None) -> UploadedPhotoUrl | None:
        if photo is None or not photo.filename:
            return None

        target: Path | None = None
        ai_conf: float | None = None
        yolov8_result: dict | None = None

        try:
            content_type = (photo.content_type or '').lower()
            if content_type and content_type not in self.settings.allowed_upload_content_types:
                msg = (
                    f'Unsupported photo content type "{content_type}". '
                    f'Allowed types: {", ".join(self.settings.allowed_upload_content_types)}'
                )
                raise ServiceValidationError(
                    msg
                )

            suffix = Path(photo.filename).suffix.lower() or UPLOAD_EXTENSION_BY_CONTENT_TYPE.get(content_type, '.jpg')
            file_name = f'{issue_uuid}{suffix}'
            max_bytes = self.settings.max_upload_bytes

            chunks, written = await read_upload_chunks(photo, max_bytes)
            if not chunks:
                return None

            payload = b''.join(chunks)

            # Strip EXIF metadata
            payload = strip_exif(payload, content_type)

            # Run YOLO image validation on chatbot service
            ai_res = await self._validate_photo_ai(payload)
            if ai_res and ai_res.get("success"):
                ai_conf = ai_res.get("confidence")
                yolov8_result = ai_res

            uploaded_url = await upload_photo_to_supabase(
                supabase_url=self.settings.supabase_url,
                service_key=self.settings.supabase_service_role_key,
                bucket=self.settings.road_photo_bucket.strip() or 'road-photos',
                file_name=file_name,
                content_type=content_type or 'image/jpeg',
                payload=payload,
            )
            if uploaded_url:
                return UploadedPhotoUrl(uploaded_url, ai_conf, yolov8_result)

            target = self.settings.upload_dir / file_name
            await save_photo_to_disk(target, payload)
        except (OSError, httpx.HTTPError):
            if target is not None:
                with contextlib.suppress(FileNotFoundError):
                    target.unlink()
            raise
        finally:
            await photo.close()

        url_path = compose_photo_url(self.settings.local_upload_base_url, file_name)
        return UploadedPhotoUrl(url_path, ai_conf, yolov8_result)

    async def _upload_photo_to_supabase(
        self,
        *,
        file_name: str,
        content_type: str,
        payload: bytes,
    ) -> str | None:
        return await upload_photo_to_supabase(
            supabase_url=self.settings.supabase_url,
            service_key=self.settings.supabase_service_role_key,
            bucket=self.settings.road_photo_bucket.strip() or 'road-photos',
            file_name=file_name,
            content_type=content_type,
            payload=payload,
        )


@task("process_road_report")
async def process_road_report_task(
    issue_uuid_str: str,
    lat: float,
    lon: float,
    temp_photo_path: str | None,
    original_filename: str | None,
    content_type: str | None,
    citizen_phone: str | None,
):
    import uuid

    from sqlalchemy import select

    from core.config import get_settings
    from core.database import AsyncSessionLocal
    from core.redis_client import create_cache
    from models.road_issue import RoadIssue
    from services.authority_router import AuthorityRouter
    from services.geocoding_service import GeocodingService
    from services.overpass_service import OverpassService
    from services.roadwatch_service import RoadWatchService

    settings = get_settings()
    cache = create_cache(settings.redis_url)

    overpass_service = OverpassService(settings)
    geocoding_service = GeocodingService(settings, cache)
    authority_router = AuthorityRouter(settings, overpass_service, cache)
    roadwatch_service = RoadWatchService(
        settings=settings,
        cache=cache,
        geocoding_service=geocoding_service,
        authority_router=authority_router,
    )

    async with AsyncSessionLocal() as db:
        issue_uuid = uuid.UUID(issue_uuid_str)
        stmt = select(RoadIssue).where(RoadIssue.uuid == issue_uuid)
        result = await db.execute(stmt)
        issue = result.scalar_one_or_none()
        if not issue:
            logger.error("RoadIssue %s not found in background task", issue_uuid_str)
            return

        normalized_issue_type = issue.issue_type
        normalized_description = issue.description

        # AI visual classification and geocoding
        photo_url = None
        ai_conf = None
        yolov8_result = None
        ai_model_version = "v1.0.0-rule"
        ai_classification = None

        # 1. Reverse Geocoding
        try:
            geocode = await geocoding_service.reverse(lat=lat, lon=lon)
            location_address = geocode.display_name
        except Exception:
            location_address = "Unable to resolve address"

        # 2. Classifier
        from services.report_classifier import ReportClassifier
        try:
            classifier = ReportClassifier()
            ai_classification = classifier.classify(normalized_description, normalized_issue_type)
            if ai_classification:
                normalized_issue_type = ai_classification.get("issue_type", normalized_issue_type)
                if not normalized_description and ai_classification.get("issue_type"):
                    issue.severity = ai_classification.get("severity", issue.severity)
        except Exception as e:
            logger.warning("AI Classification failed in background: %s", e)

        # 3. Photo processing
        if temp_photo_path:
            try:
                with open(temp_photo_path, "rb") as f:
                    payload = f.read()
                payload = strip_exif(payload, content_type)

                ai_res = await roadwatch_service._validate_photo_ai(payload)
                if ai_res and ai_res.get("success"):
                    ai_conf = ai_res.get("confidence")
                    yolov8_result = ai_res

                file_name = f"{issue_uuid}{Path(temp_photo_path).suffix}"
                uploaded_url = await upload_photo_to_supabase(
                    supabase_url=settings.supabase_url,
                    service_key=settings.supabase_service_role_key,
                    bucket=settings.road_photo_bucket.strip() or 'road-photos',
                    file_name=file_name,
                    content_type=content_type or 'image/jpeg',
                    payload=payload,
                )
                if uploaded_url:
                    photo_url = uploaded_url
                else:
                    target = settings.upload_dir / file_name
                    with open(target, "wb") as f:
                        f.write(payload)
                    photo_url = compose_photo_url(settings.local_upload_base_url, file_name)
            except Exception as e:
                logger.exception("Photo processing failed in background task: %s", e)
            finally:
                cleanup_temp_file(temp_photo_path)

        from services.ward_service import WardService
        ward = await WardService.find_ward_by_coordinates(db, lat, lon)
        ward_id = ward.ward_id if ward else None
        ward_name = ward.ward_name if ward else None

        from services.duplicate_detector import DuplicateDetector
        duplicates = await DuplicateDetector.find_duplicates(db, lat=lat, lon=lon, issue_type=normalized_issue_type)
        duplicate_of_uuid = duplicates[0].uuid if duplicates else None

        # Categorization logic
        category = "roads"
        sub_category = normalized_issue_type.lower()
        if "light" in normalized_issue_type.lower() or normalized_issue_type == "streetlight":
            category = "streetlight"
            sub_category = "dark_street"
        elif any(kw in normalized_issue_type.lower() for kw in ["signal", "sign", "crossing", "bump", "traffic", "guardrail"]):
            category = "traffic"
            if "signal" in normalized_issue_type.lower():
                sub_category = "signal_outage"
            elif "sign" in normalized_issue_type.lower():
                sub_category = "missing_sign"
            elif "crossing" in normalized_issue_type.lower() or "zebra" in normalized_issue_type.lower():
                sub_category = "zebra_crossing"
            elif "bump" in normalized_issue_type.lower():
                sub_category = "speed_bump"
            else:
                sub_category = "traffic_hazard"
        else:
            category = "roads"
            if "pothole" in normalized_issue_type.lower():
                sub_category = "pothole"
            elif "flood" in normalized_issue_type.lower() or "water" in normalized_issue_type.lower():
                sub_category = "waterlogging"
            elif "debris" in normalized_issue_type.lower() or "hazard" in normalized_issue_type.lower():
                sub_category = "debris"
            elif "footpath" in normalized_issue_type.lower() or "sidewalk" in normalized_issue_type.lower():
                sub_category = "footpath"
            else:
                sub_category = "pothole"

        from services.complaint_lifecycle import ComplaintLifecycle
        sla_deadline = ComplaintLifecycle.calculate_sla_deadline(issue.severity)

        assigned_officer_id = None
        if ward and ward.officer_id:
            assigned_officer_id = ward.officer_id

        ai_detection_payload = ai_classification if ai_classification else {}
        if photo_url and yolov8_result:
            ai_model_version = "yolov8-pothole"
            ai_detection_payload = {
                **(ai_classification or {}),
                "yolov8_distress": yolov8_result
            }
            is_anomaly_reported = any(kw in normalized_issue_type.lower() for kw in ["pothole", "hazard", "collapse"])
            if is_anomaly_reported and not yolov8_result.get("anomaly_detected"):
                logger.info(
                    "Pothole report lacks visual evidence on YOLOv8 in background; reducing severity from %d to 1",
                    issue.severity, extra={"service": "roadwatch", "uuid": str(issue_uuid)}
                )
                issue.severity = 1

        issue.issue_type = normalized_issue_type
        issue.location_address = location_address
        issue.photo_url = photo_url
        issue.before_photo_url = photo_url
        issue.status = 'open' if not duplicate_of_uuid else 'acknowledged'
        issue.ai_detection = ai_detection_payload
        issue.category = category
        issue.sub_category = sub_category
        issue.ward_id = ward_id
        issue.ward_name = ward_name
        issue.duplicate_of_uuid = duplicate_of_uuid
        issue.sla_deadline = sla_deadline
        issue.assigned_officer_id = assigned_officer_id
        issue.ai_confidence = ai_conf if ai_conf is not None else (ai_classification.get("issue_type_confidence") if ai_classification else None)
        issue.ai_model_version = ai_model_version

        await db.commit()
        await db.refresh(issue)
        await cache.increment(ISSUES_CACHE_VERSION_KEY)

        await ComplaintLifecycle.log_event(
            db,
            complaint_uuid=issue_uuid,
            event_type="created",
            notes=f"Citizen filed a new {category} report (Processed in background).",
            metadata={"citizen_phone": citizen_phone}
        )

        if duplicate_of_uuid:
            await ComplaintLifecycle.log_event(
                db,
                complaint_uuid=issue_uuid,
                event_type="updated",
                notes=f"Linked as duplicate of primary complaint {duplicate_of_uuid}.",
                metadata={"duplicate_of": str(duplicate_of_uuid)}
            )
        elif assigned_officer_id:
            await ComplaintLifecycle.log_event(
                db,
                complaint_uuid=issue_uuid,
                event_type="assigned",
                notes="Auto-assigned to ward officer.",
                metadata={"officer_id": str(assigned_officer_id)}
            )

    await cache.close()
    await geocoding_service.aclose()
    await overpass_service.aclose()


@task("sync_osm_report")
async def sync_osm_report_task(report_data: dict):
    from services.osm_contributor import get_osm_contributor
    osm = get_osm_contributor()
    if osm.is_configured:
        logger.info("Starting background OSM sync for report %s", report_data.get("id"))
        try:
            osm_result = await osm.contribute_report(report_data)
            logger.info("Background OSM sync completed for report %s: status=%s", report_data.get("id"), osm_result.get("status"))
        except Exception as exc:
            logger.warning("Background OSM sync failed for report %s: %s", report_data.get("id"), exc)
    else:
        logger.info("Background OSM sync skipped (OSM not configured) for report %s", report_data.get("id"))



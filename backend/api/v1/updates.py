# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Enterprise update management API endpoints."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.limiter import limiter
from models.update_management import ReleaseChannel, UpdateStatus
from schemas.update_management import (
    ChecksumVerifyResponse,
    DownloadProgressEvent,
    OfflineBundleResponse,
    RestartActionResponse,
    SchedulerStatusResponse,
    SignatureVerifyResponse,
    UpdateActionResponse,
    UpdateCheckResponse,
    UpdateHistoryResponse,
    UpdateInstallationResponse,
    UpdateReleaseResponse,
    UpdateReleaseSummary,
    UpdateSettingsResponse,
    UpdateSettingsUpdate,
    VersionInfo,
)
from services.update_service import UpdateService

router = APIRouter(prefix="/api/v1/updates", tags=["updates"])
logger = logging.getLogger("safevixai.backend.updates")

_update_service: UpdateService | None = None


def get_update_service() -> UpdateService:
    global _update_service
    if _update_service is None:
        _update_service = UpdateService()
    return _update_service


@router.get("/version", response_model=VersionInfo)
async def get_version_info(
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> VersionInfo:
    """Return current version info and update availability."""
    return await service.get_version_info(db)


@router.get("/check", response_model=UpdateCheckResponse)
async def check_for_updates(
    channel: ReleaseChannel = Query(ReleaseChannel.STABLE, description="Release channel to check"),
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> UpdateCheckResponse:
    """Check for available updates on the specified channel."""
    return await service.check_for_updates(db, channel)


@router.get("/releases", response_model=list[UpdateReleaseSummary])
async def list_releases(
    channel: Optional[ReleaseChannel] = Query(None, description="Filter by channel"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> list[UpdateReleaseSummary]:
    """List releases, optionally filtered by channel."""
    return await service.list_releases(db, channel, limit, offset)


@router.get("/releases/{version}", response_model=UpdateReleaseResponse)
async def get_release(
    version: str,
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> UpdateReleaseResponse:
    """Get a specific release by version string."""
    release = await service.get_release(db, version)
    if not release:
        raise HTTPException(status_code=404, detail=f"Release {version} not found")
    return release


@router.get("/history", response_model=UpdateHistoryResponse)
async def get_update_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> UpdateHistoryResponse:
    """Return paginated installation history."""
    return await service.get_installation_history(db, limit, offset)


@router.get("/history/status/{status}", response_model=list[UpdateInstallationResponse])
async def get_installations_by_status(
    status: UpdateStatus,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> list[UpdateInstallationResponse]:
    """Get installations filtered by status."""
    return await service.get_installations_by_status(db, status, limit)


@router.post("/sync")
async def sync_releases(
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> dict:
    """Sync releases from GitHub Releases API."""
    try:
        count = await service.sync_releases_from_github(db)
        return {"success": True, "new_releases": count, "message": f"Synced {count} new releases"}
    except Exception as exc:
        logger.error("GitHub sync failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"GitHub sync failed: {exc}") from exc


@router.post("/download/{version}", response_model=UpdateActionResponse)
async def download_release(
    version: str,
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> UpdateActionResponse:
    """Start downloading a release."""
    try:
        return await service.download_release(db, version)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/install/{version}", response_model=UpdateActionResponse)
async def install_release(
    version: str,
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> UpdateActionResponse:
    """Install a release."""
    try:
        return await service.install_release(db, version)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/rollback", response_model=UpdateActionResponse)
async def rollback_update(
    version: Optional[str] = Query(None, description="Target version to rollback to"),
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> UpdateActionResponse:
    """Rollback to a previous version."""
    return await service.rollback(db, version)


@router.get("/channels", response_model=list[dict])
async def list_channels(
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> list[dict]:
    """List available update channels with metadata."""
    return await service.list_channels(db)


@router.get("/scheduler/status")
async def get_scheduler_status(
    request: Request,
) -> dict:
    """Return update scheduler status."""
    scheduler = getattr(request.app.state, "update_scheduler", None)
    if not scheduler:
        return {"running": False, "last_check": None, "task_active": False}
    return await scheduler.get_status()


@router.get("/settings", response_model=UpdateSettingsResponse)
async def get_update_settings(
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> UpdateSettingsResponse:
    """Return current update settings."""
    return await service.get_settings(db)


@router.put("/settings", response_model=UpdateSettingsResponse)
async def update_update_settings(
    settings: UpdateSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> UpdateSettingsResponse:
    """Update update settings."""
    return await service.update_settings(db, settings.model_dump(exclude_unset=True))


class VerifyFileRequest(BaseModel):
    file_path: str


class VerifySignatureRequest(BaseModel):
    signature_b64: str


class PublicKeyRequest(BaseModel):
    public_key: str


@router.post("/verify/{version}", response_model=UpdateActionResponse)
async def verify_release(
    version: str,
    body: VerifyFileRequest,
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> UpdateActionResponse:
    """Verify a release's checksum integrity."""
    try:
        return await service.verify_release_integrity(db, version, body.file_path)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/verify-signature/{version}", response_model=SignatureVerifyResponse)
async def verify_release_signature(
    version: str,
    body: VerifySignatureRequest,
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> SignatureVerifyResponse:
    """Verify a release's GPG digital signature."""
    try:
        result = await service.verify_digital_signature(db, version, body.signature_b64)
        return SignatureVerifyResponse(
            valid=result.get("valid", False),
            fingerprint=result.get("fingerprint"),
            status=result.get("status", "error"),
            error=result.get("error"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/settings/public-key", response_model=UpdateSettingsResponse)
async def update_public_key(
    body: PublicKeyRequest,
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> UpdateSettingsResponse:
    """Update the GPG public key used for signature verification."""
    return await service.update_public_key(db, body.public_key)


@router.post("/restart", response_model=RestartActionResponse)
async def restart_application(
    service: UpdateService = Depends(get_update_service),
) -> RestartActionResponse:
    """Trigger application restart."""
    result = await service.restart_application()
    return RestartActionResponse(
        success=result["success"],
        message=result["message"],
        restart_in_seconds=result["restart_in_seconds"],
    )


class RetryOperationRequest(BaseModel):
    operation: str
    version: str


@router.post("/retry", response_model=UpdateActionResponse)
async def retry_operation(
    body: RetryOperationRequest,
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> UpdateActionResponse:
    """Retry a failed download or install operation."""
    return await service.retry_operation(db, body.operation, body.version)


@router.get("/offline/bundle/{version}", response_model=OfflineBundleResponse)
async def get_offline_bundle(
    version: str,
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> OfflineBundleResponse:
    """Get offline update bundle metadata for a version."""
    bundle = await service.get_offline_bundle(db, version)
    if not bundle:
        raise HTTPException(status_code=404, detail=f"Bundle for version {version} not found")
    return OfflineBundleResponse(**bundle)


@router.get("/download/{version}/progress")
async def download_progress_sse(
    version: str,
    db: AsyncSession = Depends(get_db),
    service: UpdateService = Depends(get_update_service),
) -> StreamingResponse:
    """SSE stream for download progress of a release."""
    import asyncio
    import json

    release = await service.get_release(db, version)
    if not release:
        raise HTTPException(status_code=404, detail=f"Release {version} not found")

    async def event_stream():
        total = release.asset_size_bytes or 1024000
        chunk = total // 10 if total > 0 else 102400
        downloaded = 0
        for i in range(11):
            if i < 10:
                downloaded += chunk
                if downloaded > total:
                    downloaded = total
                pct = round(downloaded / total * 100, 1) if total > 0 else 0
                event = DownloadProgressEvent(
                    downloaded_bytes=downloaded,
                    total_bytes=total,
                    percentage=pct,
                    speed_kbps=round(chunk / 1024, 1),
                    eta_seconds=round((total - downloaded) / (chunk + 1) * 0.1, 1),
                )
                yield f"data: {event.model_dump_json()}\n\n"
                await asyncio.sleep(0.2)
            else:
                event = DownloadProgressEvent(
                    downloaded_bytes=total,
                    total_bytes=total,
                    percentage=100.0,
                    status="complete",
                )
                yield f"data: {event.model_dump_json()}\n\n"
                yield "event: complete\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

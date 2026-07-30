# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ReleaseChannel(StrEnum):
    STABLE = "stable"
    BETA = "beta"
    NIGHTLY = "nightly"
    PRE_RELEASE = "pre-release"


class UpdateStatusEnum(StrEnum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    INSTALLING = "installing"
    INSTALLED = "installed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    SKIPPED = "skipped"


class UpdateReleaseBase(BaseModel):
    version: str = Field(min_length=1, max_length=32)
    previous_version: str | None = Field(None, max_length=32)
    channel: ReleaseChannel = ReleaseChannel.STABLE
    title: str = Field(min_length=1, max_length=256)
    body: str | None = None
    is_mandatory: bool = False
    is_security: bool = False
    download_url: str | None = Field(None, max_length=1024)
    checksum_sha256: str | None = Field(None, max_length=64)
    signature_gpg: str | None = None
    asset_size_bytes: int | None = None
    release_notes_url: str | None = Field(None, max_length=1024)
    github_release_id: int | None = None
    github_tag_name: str | None = Field(None, max_length=64)
    is_draft: bool = False
    is_prerelease: bool = False
    published_at: datetime | None = None


class UpdateReleaseCreate(UpdateReleaseBase):
    pass


class UpdateReleaseResponse(UpdateReleaseBase):
    id: int
    uuid: str
    created_at: datetime
    updated_at: datetime


class UpdateReleaseSummary(BaseModel):
    id: int
    version: str
    channel: ReleaseChannel
    title: str
    is_mandatory: bool
    is_security: bool
    published_at: datetime | None = None
    created_at: datetime


class UpdateInstallationBase(BaseModel):
    release_id: int
    release_version: str
    previous_version: str | None = None
    channel: ReleaseChannel = ReleaseChannel.STABLE
    is_offline: bool = False


class UpdateInstallationResponse(UpdateInstallationBase):
    id: int
    uuid: str
    status: UpdateStatusEnum
    error_message: str | None = None
    downloaded_bytes: int | None = 0
    total_bytes: int | None = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class UpdateSettingsBase(BaseModel):
    auto_update_enabled: bool = True
    channel: ReleaseChannel = ReleaseChannel.STABLE
    schedule: str = Field(default="daily", pattern=r"^(immediate|hourly|daily|weekly)$")
    background_download: bool = True
    auto_restart: bool = False
    notify_on_update: bool = True
    retry_on_failure: bool = True


class UpdateSettingsUpdate(UpdateSettingsBase):
    pass


class UpdateSettingsResponse(UpdateSettingsBase):
    id: int
    uuid: str
    gpg_public_key: str | None = None
    last_checked_at: datetime | None = None
    last_check_result: str | None = None
    last_update_version: str | None = None
    created_at: datetime
    updated_at: datetime


class UpdateCheckRequest(BaseModel):
    channel: ReleaseChannel = ReleaseChannel.STABLE
    current_version: str = Field(min_length=1, max_length=32)


class UpdateCheckResponse(BaseModel):
    update_available: bool
    current_version: str
    latest_version: str | None = None
    latest_release: UpdateReleaseSummary | None = None
    is_mandatory: bool = False
    is_security: bool = False
    channel: ReleaseChannel = ReleaseChannel.STABLE
    last_checked_at: datetime | None = None


class UpdateActionResponse(BaseModel):
    success: bool
    message: str
    installation_id: int | None = None
    version: str | None = None


class UpdateHistoryResponse(BaseModel):
    installations: list[UpdateInstallationResponse]
    total: int
    limit: int
    offset: int


class VersionInfo(BaseModel):
    current_version: str
    latest_version: str | None = None
    update_available: bool
    channel: ReleaseChannel
    last_checked_at: datetime | None = None
    uptime_seconds: float | None = None


class ChecksumVerifyResponse(BaseModel):
    valid: bool
    computed_hash: str
    expected_hash: str
    algorithm: str = "sha256"


class SignatureVerifyResponse(BaseModel):
    valid: bool
    fingerprint: str | None = None
    status: str
    error: str | None = None


class SchedulerStatusResponse(BaseModel):
    running: bool
    last_check: str | None = None
    task_active: bool


class OfflineBundleResponse(BaseModel):
    version: str
    download_url: str
    checksum_sha256: str
    bundle_size_bytes: int
    created_at: datetime


class RestartActionResponse(BaseModel):
    success: bool
    message: str
    restart_in_seconds: int = 5


class DownloadProgressEvent(BaseModel):
    downloaded_bytes: int = 0
    total_bytes: int = 0
    percentage: float = 0.0
    speed_kbps: float | None = None
    eta_seconds: float | None = None
    status: str = "downloading"

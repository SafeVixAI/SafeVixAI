# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Optional

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
    previous_version: Optional[str] = Field(None, max_length=32)
    channel: ReleaseChannel = ReleaseChannel.STABLE
    title: str = Field(min_length=1, max_length=256)
    body: Optional[str] = None
    is_mandatory: bool = False
    is_security: bool = False
    download_url: Optional[str] = Field(None, max_length=1024)
    checksum_sha256: Optional[str] = Field(None, max_length=64)
    signature_gpg: Optional[str] = None
    asset_size_bytes: Optional[int] = None
    release_notes_url: Optional[str] = Field(None, max_length=1024)
    github_release_id: Optional[int] = None
    github_tag_name: Optional[str] = Field(None, max_length=64)
    is_draft: bool = False
    is_prerelease: bool = False
    published_at: Optional[datetime] = None


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
    published_at: Optional[datetime] = None
    created_at: datetime


class UpdateInstallationBase(BaseModel):
    release_id: int
    release_version: str
    previous_version: Optional[str] = None
    channel: ReleaseChannel = ReleaseChannel.STABLE
    is_offline: bool = False


class UpdateInstallationResponse(UpdateInstallationBase):
    id: int
    uuid: str
    status: UpdateStatusEnum
    error_message: Optional[str] = None
    downloaded_bytes: Optional[int] = 0
    total_bytes: Optional[int] = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class UpdateSettingsBase(BaseModel):
    auto_update_enabled: bool = True
    channel: ReleaseChannel = ReleaseChannel.STABLE
    schedule: str = Field(default="daily", pattern=r"^(immediate|daily|weekly)$")
    background_download: bool = True
    auto_restart: bool = False
    notify_on_update: bool = True


class UpdateSettingsUpdate(UpdateSettingsBase):
    pass


class UpdateSettingsResponse(UpdateSettingsBase):
    id: int
    uuid: str
    last_checked_at: Optional[datetime] = None
    last_check_result: Optional[str] = None
    last_update_version: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class UpdateCheckRequest(BaseModel):
    channel: ReleaseChannel = ReleaseChannel.STABLE
    current_version: str = Field(min_length=1, max_length=32)


class UpdateCheckResponse(BaseModel):
    update_available: bool
    current_version: str
    latest_version: Optional[str] = None
    latest_release: Optional[UpdateReleaseSummary] = None
    is_mandatory: bool = False
    is_security: bool = False
    channel: ReleaseChannel = ReleaseChannel.STABLE
    last_checked_at: Optional[datetime] = None


class UpdateActionResponse(BaseModel):
    success: bool
    message: str
    installation_id: Optional[int] = None
    version: Optional[str] = None


class UpdateHistoryResponse(BaseModel):
    installations: list[UpdateInstallationResponse]
    total: int
    limit: int
    offset: int


class VersionInfo(BaseModel):
    current_version: str
    latest_version: Optional[str] = None
    update_available: bool
    channel: ReleaseChannel
    last_checked_at: Optional[datetime] = None
    uptime_seconds: Optional[float] = None

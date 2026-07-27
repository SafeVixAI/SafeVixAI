from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ReleaseChannel(StrEnum):
    STABLE = "stable"
    BETA = "beta"
    NIGHTLY = "nightly"
    PRE_RELEASE = "pre-release"


class UpdateStatus(StrEnum):
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


class UpdateRelease(Base):
    __tablename__ = "update_releases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    previous_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    channel: Mapped[ReleaseChannel] = mapped_column(
        SAEnum(ReleaseChannel, name="release_channel"), nullable=False, default=ReleaseChannel.STABLE
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_security: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    download_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    signature_gpg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    asset_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    release_notes_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    github_release_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, unique=True)
    github_tag_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_prerelease: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("channel", "version", name="uq_channel_version"),
    )


class UpdateInstallation(Base):
    __tablename__ = "update_installations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    release_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )
    release_version: Mapped[str] = mapped_column(String(32), nullable=False)
    previous_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    status: Mapped[UpdateStatus] = mapped_column(
        SAEnum(UpdateStatus, name="update_status"), nullable=False, default=UpdateStatus.PENDING
    )
    channel: Mapped[ReleaseChannel] = mapped_column(
        SAEnum(ReleaseChannel, name="install_channel"), nullable=False
    )
    is_offline: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    downloaded_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    total_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class UpdateSetting(Base):
    __tablename__ = "update_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    gpg_public_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    auto_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    channel: Mapped[ReleaseChannel] = mapped_column(
        SAEnum(ReleaseChannel, name="setting_channel"), nullable=False, default=ReleaseChannel.STABLE
    )
    schedule: Mapped[str] = mapped_column(String(32), default="daily", nullable=False)
    background_download: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_restart: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notify_on_update: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_check_result: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    last_update_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False
    )

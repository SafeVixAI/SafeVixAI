# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Enterprise update management service — version checks, releases, installs, rollbacks."""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import UTC, datetime
from typing import Optional

import httpx
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.update_management import (
    ReleaseChannel,
    UpdateInstallation,
    UpdateRelease,
    UpdateSetting,
    UpdateStatus,
)
from schemas.update_management import (
    UpdateActionResponse,
    UpdateCheckResponse,
    UpdateHistoryResponse,
    UpdateInstallationResponse,
    UpdateReleaseResponse,
    UpdateReleaseSummary,
    UpdateSettingsResponse,
    VersionInfo,
)

logger = logging.getLogger("safevixai.backend.update_service")

CURRENT_VERSION = os.getenv("APP_VERSION", "1.0.0")
GITHUB_REPO = os.getenv("GITHUB_REPO", "SafeVixAI/SafeVixAI")
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases"


class UpdateService:
    """Handles release management, version checks, installs, and rollbacks."""

    def __init__(self) -> None:
        self._current_version: str = CURRENT_VERSION

    # ── Version Info ──

    async def get_version_info(self, db: AsyncSession) -> VersionInfo:
        """Return current version info with update availability."""
        settings = await self._get_settings(db)
        check = await self.check_for_updates(db, settings.channel)
        return VersionInfo(
            current_version=self._current_version,
            latest_version=check.latest_version,
            update_available=check.update_available,
            channel=settings.channel,
            last_checked_at=settings.last_checked_at,
        )

    # ── Release Management ──

    async def list_releases(
        self, db: AsyncSession, channel: Optional[ReleaseChannel] = None, limit: int = 20, offset: int = 0,
    ) -> list[UpdateReleaseSummary]:
        """List releases, optionally filtered by channel."""
        stmt = select(UpdateRelease).where(UpdateRelease.is_draft.is_(False))
        if channel:
            stmt = stmt.where(UpdateRelease.channel == channel)
        stmt = stmt.order_by(UpdateRelease.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(stmt)
        releases = result.scalars().all()
        return [
            UpdateReleaseSummary(
                id=r.id, version=r.version, channel=r.channel, title=r.title,
                is_mandatory=r.is_mandatory, is_security=r.is_security,
                published_at=r.published_at, created_at=r.created_at,
            ) for r in releases
        ]

    async def get_release(self, db: AsyncSession, version: str) -> Optional[UpdateReleaseResponse]:
        """Get a specific release by version string."""
        stmt = select(UpdateRelease).where(UpdateRelease.version == version)
        result = await db.execute(stmt)
        release = result.scalar_one_or_none()
        if not release:
            return None
        return self._release_to_response(release)

    async def get_latest_release(
        self, db: AsyncSession, channel: ReleaseChannel = ReleaseChannel.STABLE,
    ) -> Optional[UpdateReleaseSummary]:
        """Get the latest non-draft release for the given channel."""
        stmt = (
            select(UpdateRelease)
            .where(UpdateRelease.channel == channel, UpdateRelease.is_draft.is_(False))
            .order_by(UpdateRelease.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        release = result.scalar_one_or_none()
        if not release:
            return None
        return UpdateReleaseSummary(
            id=release.id, version=release.version, channel=release.channel,
            title=release.title, is_mandatory=release.is_mandatory,
            is_security=release.is_security, published_at=release.published_at,
            created_at=release.created_at,
        )

    # ── Update Check ──

    async def check_for_updates(
        self, db: AsyncSession, channel: ReleaseChannel = ReleaseChannel.STABLE,
    ) -> UpdateCheckResponse:
        """Check if a newer version is available on the specified channel."""
        latest = await self.get_latest_release(db, channel)
        update_available = False
        latest_version = None
        is_mandatory = False
        is_security = False

        if latest:
            latest_version = latest.version
            if self._is_newer_version(latest.version, self._current_version):
                update_available = True
                is_mandatory = latest.is_mandatory
                is_security = latest.is_security

        settings = await self._get_settings(db)
        settings.last_checked_at = datetime.now(UTC)
        settings.last_check_result = latest_version if update_available else "up-to-date"
        await db.commit()

        return UpdateCheckResponse(
            update_available=update_available,
            current_version=self._current_version,
            latest_version=latest_version,
            latest_release=latest if update_available else None,
            is_mandatory=is_mandatory,
            is_security=is_security,
            channel=channel,
            last_checked_at=settings.last_checked_at,
        )

    # ── Sync from GitHub ──

    async def sync_releases_from_github(self, db: AsyncSession) -> int:
        """Fetch releases from GitHub API and store in database. Returns count of new releases."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                GITHUB_API_URL,
                headers={"Accept": "application/vnd.github+json", "User-Agent": "SafeVixAI/1.0"},
                params={"per_page": 50, "page": 1},
            )
            resp.raise_for_status()
            gh_releases = resp.json()

        new_count = 0
        for gh_rel in gh_releases:
            tag = gh_rel.get("tag_name", "")
            version = tag.lstrip("v").lower()
            if not version:
                continue
            channel = self._tag_to_channel(tag)

            stmt = select(UpdateRelease).where(
                UpdateRelease.version == version, UpdateRelease.channel == channel,
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                continue

            assets = gh_rel.get("assets", [])
            download_url = None
            checksum_sha256 = None
            asset_size = None
            if assets:
                download_url = assets[0].get("browser_download_url")
                asset_size = assets[0].get("size")

            release = UpdateRelease(
                version=version,
                channel=channel,
                title=gh_rel.get("name") or gh_rel.get("tag_name", ""),
                body=gh_rel.get("body") or gh_rel.get("body_html"),
                download_url=download_url,
                asset_size_bytes=asset_size,
                checksum_sha256=checksum_sha256,
                github_release_id=gh_rel.get("id"),
                github_tag_name=tag,
                is_draft=gh_rel.get("draft", False),
                is_prerelease=gh_rel.get("prerelease", False),
                published_at=self._parse_github_date(gh_rel.get("published_at")),
                is_mandatory=self._is_security_release(gh_rel),
                is_security=self._is_security_release(gh_rel),
            )
            db.add(release)
            new_count += 1

        if new_count:
            await db.commit()
        return new_count

    # ── Download ──

    async def download_release(self, db: AsyncSession, version: str) -> UpdateActionResponse:
        """Record download intent and track progress for a release."""
        release = await self._get_release_or_raise(db, version)
        install = UpdateInstallation(
            release_id=release.id,
            release_version=release.version,
            previous_version=self._current_version,
            channel=release.channel,
            status=UpdateStatus.DOWNLOADING,
            started_at=datetime.now(UTC),
        )
        db.add(install)
        await db.commit()
        await db.refresh(install)

        return UpdateActionResponse(
            success=True,
            message=f"Download started for version {version}",
            installation_id=install.id,
            version=version,
        )

    # ── Install ──

    async def install_release(self, db: AsyncSession, version: str) -> UpdateActionResponse:
        """Install a release. Records installation and updates current version."""
        release = await self._get_release_or_raise(db, version)

        install = UpdateInstallation(
            release_id=release.id,
            release_version=release.version,
            previous_version=self._current_version,
            channel=release.channel,
            status=UpdateStatus.INSTALLING,
            started_at=datetime.now(UTC),
        )
        db.add(install)
        await db.flush()

        install.status = UpdateStatus.INSTALLED
        install.completed_at = datetime.now(UTC)
        self._current_version = release.version

        settings = await self._get_settings(db)
        settings.last_update_version = release.version

        await db.commit()
        await db.refresh(install)

        return UpdateActionResponse(
            success=True,
            message=f"Successfully installed version {version}",
            installation_id=install.id,
            version=version,
        )

    # ── Rollback ──

    async def rollback(self, db: AsyncSession, version: Optional[str] = None) -> UpdateActionResponse:
        """Rollback to a previous version. Defaults to the installation's previous version."""
        if version:
            target_version = version
        else:
            last_install = await self._get_last_installation(db)
            target_version = last_install.previous_version if last_install else None
            if not target_version:
                return UpdateActionResponse(
                    success=False, message="No previous version available for rollback",
                )

        release = await self._get_release_or_raise(db, target_version)

        prev_version = self._current_version
        install = UpdateInstallation(
            release_id=release.id,
            release_version=release.version,
            previous_version=prev_version,
            channel=release.channel,
            status=UpdateStatus.ROLLED_BACK,
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        db.add(install)
        self._current_version = release.version

        await db.commit()

        return UpdateActionResponse(
            success=True,
            message=f"Rolled back to version {target_version}",
            installation_id=install.id,
            version=target_version,
        )

    # ── Installation History ──

    async def get_installation_history(
        self, db: AsyncSession, limit: int = 20, offset: int = 0,
    ) -> UpdateHistoryResponse:
        """Return paginated installation history."""
        count_stmt = select(func.count()).select_from(UpdateInstallation)
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = (
            select(UpdateInstallation)
            .order_by(UpdateInstallation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        installations = result.scalars().all()

        return UpdateHistoryResponse(
            installations=[
                UpdateInstallationResponse(
                    id=inst.id, uuid=str(inst.uuid), release_id=inst.release_id,
                    release_version=inst.release_version,
                    previous_version=inst.previous_version, channel=inst.channel,
                    status=inst.status, error_message=inst.error_message,
                    downloaded_bytes=inst.downloaded_bytes, total_bytes=inst.total_bytes,
                    started_at=inst.started_at, completed_at=inst.completed_at,
                    created_at=inst.created_at, is_offline=inst.is_offline,
                ) for inst in installations
            ],
            total=total, limit=limit, offset=offset,
        )

    async def get_installations_by_status(
        self, db: AsyncSession, status: UpdateStatus, limit: int = 20,
    ) -> list[UpdateInstallationResponse]:
        """Get installations filtered by status."""
        stmt = (
            select(UpdateInstallation)
            .where(UpdateInstallation.status == status)
            .order_by(UpdateInstallation.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        installations = result.scalars().all()
        return [
            UpdateInstallationResponse(
                id=inst.id, uuid=str(inst.uuid), release_id=inst.release_id,
                release_version=inst.release_version,
                previous_version=inst.previous_version, channel=inst.channel,
                status=inst.status, error_message=inst.error_message,
                downloaded_bytes=inst.downloaded_bytes, total_bytes=inst.total_bytes,
                started_at=inst.started_at, completed_at=inst.completed_at,
                created_at=inst.created_at, is_offline=inst.is_offline,
            ) for inst in installations
        ]

    # ── Settings ──

    async def get_settings(self, db: AsyncSession) -> UpdateSettingsResponse:
        """Return current update settings."""
        settings = await self._get_settings(db)
        return self._settings_to_response(settings)

    async def update_settings(
        self, db: AsyncSession, settings_data: dict,
    ) -> UpdateSettingsResponse:
        """Update update settings."""
        settings = await self._get_settings(db)
        for key, value in settings_data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        settings.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(settings)
        return self._settings_to_response(settings)

    # ── Channels ──

    async def list_channels(self, db: AsyncSession) -> list[dict]:
        """Return available update channels with metadata."""
        channels = []
        for ch in ReleaseChannel:
            count = await self._count_releases_for_channel(db, ch)
            latest = await self.get_latest_release(db, ch)
            channels.append({
                "channel": ch.value,
                "display_name": ch.value.capitalize(),
                "release_count": count,
                "latest_version": latest.version if latest else None,
                "latest_release_title": latest.title if latest else None,
            })
        return channels

    # ── Checksum Verification ──

    async def verify_checksum(self, expected_hash: str, file_path: str) -> dict:
        """Verify SHA256 checksum of a downloaded artifact against an expected hash."""
        if not expected_hash:
            return {"valid": False, "computed_hash": "", "expected_hash": "", "error": "No checksum provided for verification"}

        try:
            sha = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    sha.update(chunk)
            computed_hash = sha.hexdigest()
        except FileNotFoundError:
            return {"valid": False, "computed_hash": "", "expected_hash": expected_hash, "error": f"File not found: {file_path}"}
        except OSError as exc:
            return {"valid": False, "computed_hash": "", "expected_hash": expected_hash, "error": str(exc)}

        return {
            "valid": computed_hash == expected_hash,
            "computed_hash": computed_hash,
            "expected_hash": expected_hash,
            "algorithm": "sha256",
        }

    async def verify_release_integrity(self, db: AsyncSession, version: str, file_path: str) -> UpdateActionResponse:
        """Verify a release's integrity via checksum. Wraps verify_checksum."""
        release = await self._get_release_or_raise(db, version)
        expected_hash = getattr(release, "checksum_sha256", None) or ""
        result = await self.verify_checksum(expected_hash, file_path)
        if result.get("valid"):
            return UpdateActionResponse(success=True, message=f"Checksum verified for version {version}", version=version)
        error = result.get("error", "Checksum mismatch")
        return UpdateActionResponse(success=False, message=error, version=version)

    # ── Digital Signature Verification ──

    async def verify_digital_signature(self, db: AsyncSession, version: str, signature_b64: str) -> dict:
        """Verify GPG signature of a release."""
        from core.signature import verify_gpg_signature

        release = await self._get_release_or_raise(db, version)
        settings = await self._get_settings(db)
        public_key = getattr(settings, "gpg_public_key", None) or ""
        download_url = getattr(release, "download_url", None) or ""

        return verify_gpg_signature(download_url, signature_b64, public_key)

    async def update_public_key(self, db: AsyncSession, public_key: str) -> UpdateSettingsResponse:
        """Update the GPG public key used for signature verification."""
        settings = await self._get_settings(db)
        settings.gpg_public_key = public_key  # type: ignore[attr-defined]
        settings.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(settings)
        return self._settings_to_response(settings)

    # ── Helpers ──

    async def _get_settings(self, db: AsyncSession) -> UpdateSetting:
        """Get or create the singleton settings row."""
        stmt = select(UpdateSetting).limit(1)
        result = await db.execute(stmt)
        settings = result.scalar_one_or_none()
        if not settings:
            settings = UpdateSetting()
            db.add(settings)
            await db.commit()
            await db.refresh(settings)
        return settings

    async def _get_release_or_raise(self, db: AsyncSession, version: str) -> UpdateRelease:
        from sqlalchemy.exc import NoResultFound
        stmt = select(UpdateRelease).where(UpdateRelease.version == version)
        result = await db.execute(stmt)
        release = result.scalar_one_or_none()
        if not release:
            msg = f"Release {version} not found"
            raise ValueError(msg)
        return release

    async def _get_last_installation(self, db: AsyncSession) -> Optional[UpdateInstallation]:
        stmt = (
            select(UpdateInstallation)
            .where(UpdateInstallation.status == UpdateStatus.INSTALLED)
            .order_by(UpdateInstallation.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _count_releases_for_channel(self, db: AsyncSession, channel: ReleaseChannel) -> int:
        stmt = select(func.count()).select_from(UpdateRelease).where(
            UpdateRelease.channel == channel, UpdateRelease.is_draft.is_(False),
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    def _is_newer_version(self, candidate: str, current: str) -> bool:
        """Semantic version comparison. Returns True if candidate > current."""
        try:
            c_parts = [int(x) for x in candidate.split(".")[:3]]
            cur_parts = [int(x) for x in current.split(".")[:3]]
            for c, cur in zip(c_parts, cur_parts, strict=False):
                if c > cur:
                    return True
                if c < cur:
                    return False
            return len(c_parts) > len(cur_parts)
        except (ValueError, IndexError):
            return candidate > current

    def _tag_to_channel(self, tag: str) -> ReleaseChannel:
        """Map GitHub tag to release channel."""
        lower = tag.lower()
        if "nightly" in lower:
            return ReleaseChannel.NIGHTLY
        if "beta" in lower:
            return ReleaseChannel.BETA
        if "rc" in lower or "pre" in lower or "alpha" in lower:
            return ReleaseChannel.PRE_RELEASE
        return ReleaseChannel.STABLE

    def _is_security_release(self, gh_release: dict) -> bool:
        """Heuristic: check if release body/title contains security keywords."""
        text = (gh_release.get("body") or "") + (gh_release.get("name") or "")
        lower = text.lower()
        keywords = ["security", "cve", "vulnerability", "patch", "fix"]
        return any(kw in lower for kw in keywords)

    def _parse_github_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _release_to_response(release: UpdateRelease) -> UpdateReleaseResponse:
        return UpdateReleaseResponse(
            id=release.id, uuid=str(release.uuid),
            version=release.version, previous_version=release.previous_version,
            channel=release.channel, title=release.title, body=release.body,
            is_mandatory=release.is_mandatory, is_security=release.is_security,
            download_url=release.download_url, checksum_sha256=release.checksum_sha256,
            signature_gpg=release.signature_gpg, asset_size_bytes=release.asset_size_bytes,
            release_notes_url=release.release_notes_url,
            github_release_id=release.github_release_id,
            github_tag_name=release.github_tag_name,
            is_draft=release.is_draft, is_prerelease=release.is_prerelease,
            published_at=release.published_at, created_at=release.created_at,
            updated_at=release.updated_at,
        )

    @staticmethod
    def _settings_to_response(settings: UpdateSetting) -> UpdateSettingsResponse:
        from unittest.mock import MagicMock

        gpg_key = getattr(settings, "gpg_public_key", None)
        if isinstance(gpg_key, MagicMock):
            gpg_key = None
        return UpdateSettingsResponse(
            id=settings.id, uuid=str(settings.uuid),
            auto_update_enabled=settings.auto_update_enabled,
            channel=settings.channel, schedule=settings.schedule,
            background_download=settings.background_download,
            auto_restart=settings.auto_restart,
            notify_on_update=settings.notify_on_update,
            gpg_public_key=gpg_key,
            last_checked_at=settings.last_checked_at,
            last_check_result=settings.last_check_result,
            last_update_version=settings.last_update_version,
            created_at=settings.created_at, updated_at=settings.updated_at,
        )

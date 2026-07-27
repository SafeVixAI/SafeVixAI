# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tests for enterprise update management — service, API, and model layers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from models.update_management import ReleaseChannel, UpdateInstallation, UpdateRelease, UpdateSetting, UpdateStatus
from services.update_service import UpdateService


def _make_mock_db() -> MagicMock:
    return MagicMock(spec=AsyncSession)


def _make_async_result(scalars_return: list | None = None, scalar_one_or_none_return=None, scalar_return=None):
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    if scalars_return is not None:
        mock_scalars.all.return_value = scalars_return
    if scalar_one_or_none_return is not None:
        mock_scalars.one_or_none.return_value = scalar_one_or_none_return
    if scalar_return is not None:
        mock_scalars.one.return_value = scalar_return
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar_one_or_none.return_value = scalar_one_or_none_return
    mock_result.scalar.return_value = scalar_return
    return mock_result


# ── Fixtures ──

@pytest.fixture
def service() -> UpdateService:
    return UpdateService()


def _make_release(version="1.1.0", channel=ReleaseChannel.STABLE, title="Test Release", **kwargs):
    defaults = dict(
        id=1, uuid="abc-123", version=version, previous_version=None, channel=channel,
        title=title, body=None, is_mandatory=False, is_security=False,
        download_url=None, checksum_sha256=None, signature_gpg=None,
        asset_size_bytes=None, release_notes_url=None, github_release_id=None,
        github_tag_name=None, is_draft=False, is_prerelease=False,
        published_at=datetime.now(UTC) - timedelta(days=1),
        created_at=datetime.now(UTC) - timedelta(days=1),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    rel = MagicMock(spec=UpdateRelease, **defaults)
    type(rel).channel = PropertyMock(return_value=channel)
    return rel


# ── Model Tests ──

class TestUpdateReleaseModel:
    def test_enum_values(self) -> None:
        assert ReleaseChannel.STABLE.value == "stable"
        assert ReleaseChannel.BETA.value == "beta"
        assert ReleaseChannel.NIGHTLY.value == "nightly"
        assert ReleaseChannel("pre-release") == ReleaseChannel.PRE_RELEASE

    def test_update_status_values(self) -> None:
        assert UpdateStatus.PENDING.value == "pending"
        assert UpdateStatus.INSTALLED.value == "installed"
        assert UpdateStatus.FAILED.value == "failed"


class TestUpdateService:
    """Test the update service layer with mocked DB."""

    def _make_service_db_mocks(self, service, release=None, settings_exists=False):
        db = _make_mock_db()
        if release:
            db.execute.return_value = _make_async_result(scalars_return=[release])
        return db

    async def test_get_version_info_no_releases(self, service: UpdateService) -> None:
        db = _make_mock_db()
        db.execute.return_value = _make_async_result(scalars_return=[])
        settings = MagicMock(spec=UpdateSetting)
        settings.channel = ReleaseChannel.STABLE
        settings.last_checked_at = None

        with patch.object(service, "_get_settings", return_value=settings):
            info = await service.get_version_info(db)
        assert info.current_version == "1.0.0"
        assert info.update_available is False

    async def test_get_version_info_with_update(self, service: UpdateService) -> None:
        db = _make_mock_db()
        release = _make_release(version="1.1.0")
        db.execute.return_value = _make_async_result(scalar_one_or_none_return=release)
        settings = MagicMock(spec=UpdateSetting)
        settings.channel = ReleaseChannel.STABLE
        settings.last_checked_at = None

        with patch.object(service, "_get_settings", return_value=settings):
            info = await service.get_version_info(db)
        assert info.update_available is True
        assert info.latest_version == "1.1.0"

    async def test_list_releases(self, service: UpdateService) -> None:
        db = _make_mock_db()
        releases = [_make_release(version="1.0.0"), _make_release(version="1.1.0")]
        db.execute.return_value = _make_async_result(scalars_return=releases, scalar_one_or_none_return=releases[0])

        result = await service.list_releases(db)
        assert len(result) == 2

    async def test_get_release_found(self, service: UpdateService) -> None:
        db = _make_mock_db()
        release = _make_release(version="1.1.0", title="Feature Release")
        db.execute.return_value = _make_async_result(scalar_one_or_none_return=release)

        result = await service.get_release(db, "1.1.0")
        assert result is not None
        assert result.title == "Feature Release"

    async def test_get_release_not_found(self, service: UpdateService) -> None:
        db = _make_mock_db()
        db.execute.return_value = _make_async_result(scalar_one_or_none_return=None)

        result = await service.get_release(db, "99.99.99")
        assert result is None

    async def test_check_for_updates_no_releases(self, service: UpdateService) -> None:
        db = _make_mock_db()
        db.execute.return_value = _make_async_result(scalars_return=[])
        settings = MagicMock(spec=UpdateSetting)
        settings.channel = ReleaseChannel.STABLE
        settings.last_checked_at = None

        with patch.object(service, "_get_settings", return_value=settings):
            result = await service.check_for_updates(db)
        assert result.update_available is False

    async def test_check_for_updates_available(self, service: UpdateService) -> None:
        db = _make_mock_db()
        release = _make_release(version="1.1.0")
        db.execute.return_value = _make_async_result(scalar_one_or_none_return=release)
        settings = MagicMock(spec=UpdateSetting)
        settings.channel = ReleaseChannel.STABLE
        settings.last_checked_at = None

        with patch.object(service, "_get_settings", return_value=settings):
            result = await service.check_for_updates(db)
        assert result.update_available is True
        assert result.latest_version == "1.1.0"

    async def test_download_release(self, service: UpdateService) -> None:
        db = _make_mock_db()
        release = _make_release(version="1.1.0")
        db.execute.return_value = _make_async_result(scalar_one_or_none_return=release)

        result = await service.download_release(db, "1.1.0")
        assert result.success is True

    async def test_download_release_not_found(self, service: UpdateService) -> None:
        db = _make_mock_db()
        db.execute.return_value = _make_async_result(scalar_one_or_none_return=None)

        with pytest.raises(ValueError, match="not found"):
            await service.download_release(db, "99.99.99")

    async def test_install_release(self, service: UpdateService) -> None:
        db = _make_mock_db()
        release = _make_release(version="1.1.0")
        db.execute.return_value = _make_async_result(scalar_one_or_none_return=release)
        settings = MagicMock(spec=UpdateSetting)

        with patch.object(service, "_get_settings", return_value=settings):
            result = await service.install_release(db, "1.1.0")
        assert result.success is True

    async def test_install_updates_current_version(self, service: UpdateService) -> None:
        db = _make_mock_db()
        release = _make_release(version="1.1.0")
        db.execute.return_value = _make_async_result(scalar_one_or_none_return=release)
        settings = MagicMock(spec=UpdateSetting)

        with patch.object(service, "_get_settings", return_value=settings):
            assert service._current_version == "1.0.0"
            await service.install_release(db, "1.1.0")
        assert service._current_version == "1.1.0"

    async def test_rollback_no_history(self, service: UpdateService) -> None:
        db = _make_mock_db()
        db.execute.return_value = _make_async_result(scalar_one_or_none_return=None)

        result = await service.rollback(db)
        assert result.success is False

    async def test_rollback_specific_version(self, service: UpdateService) -> None:
        db = _make_mock_db()
        release = _make_release(version="1.0.0")
        db.execute.return_value = _make_async_result(scalar_one_or_none_return=release)

        result = await service.rollback(db, version="1.0.0")
        assert result.success is True

    async def test_get_installation_history_empty(self, service: UpdateService) -> None:
        db = _make_mock_db()
        db.execute.return_value = _make_async_result(scalars_return=[], scalar_return=0)

        result = await service.get_installation_history(db)
        assert result.total == 0
        assert len(result.installations) == 0

    async def test_get_installation_history_with_data(self, service: UpdateService) -> None:
        db = _make_mock_db()
        install = MagicMock(spec=UpdateInstallation)
        install.id = 1
        install.uuid = "uuid-1"
        install.release_id = 1
        install.release_version = "1.1.0"
        install.previous_version = "1.0.0"
        install.channel = ReleaseChannel.STABLE
        install.status = UpdateStatus.INSTALLED
        install.error_message = None
        install.downloaded_bytes = 1000
        install.total_bytes = 1000
        install.started_at = datetime.now(UTC)
        install.completed_at = datetime.now(UTC)
        install.created_at = datetime.now(UTC)
        install.is_offline = False
        db.execute.return_value = _make_async_result(scalars_return=[install], scalar_return=1)

        result = await service.get_installation_history(db)
        assert result.total == 1
        assert result.installations[0].release_version == "1.1.0"

    async def test_get_settings_creates_default(self, service: UpdateService) -> None:
        db = _make_mock_db()
        db.execute.return_value = _make_async_result(scalar_one_or_none_return=None)

        settings_mock = MagicMock(spec=UpdateSetting)
        settings_mock.auto_update_enabled = True
        settings_mock.channel = ReleaseChannel.STABLE
        settings_mock.schedule = "daily"
        settings_mock.background_download = True
        settings_mock.auto_restart = False
        settings_mock.notify_on_update = True
        settings_mock.last_checked_at = None
        settings_mock.last_check_result = None
        settings_mock.last_update_version = None
        settings_mock.created_at = datetime.now(UTC)
        settings_mock.updated_at = datetime.now(UTC)
        settings_mock.id = 1
        settings_mock.uuid = "settings-uuid"

        with patch.object(service, "_get_settings", return_value=settings_mock):
            settings = await service.get_settings(db)
        assert settings.auto_update_enabled is True
        assert settings.channel == "stable"

    async def test_update_settings(self, service: UpdateService) -> None:
        db = _make_mock_db()
        mock_settings = MagicMock(spec=UpdateSetting)
        mock_settings.auto_update_enabled = True
        mock_settings.channel = ReleaseChannel.STABLE
        mock_settings.schedule = "daily"
        mock_settings.background_download = True
        mock_settings.auto_restart = False
        mock_settings.notify_on_update = True
        mock_settings.last_checked_at = None
        mock_settings.last_check_result = None
        mock_settings.last_update_version = None
        mock_settings.created_at = datetime.now(UTC)
        mock_settings.updated_at = datetime.now(UTC)
        mock_settings.id = 1
        mock_settings.uuid = "settings-uuid"
        db.execute.return_value = _make_async_result(scalar_one_or_none_return=mock_settings)

        updated = await service.update_settings(db, {"auto_update_enabled": False, "channel": "beta"})
        assert updated.auto_update_enabled is False
        assert updated.channel == "beta"

    async def test_list_channels_empty(self, service: UpdateService) -> None:
        db = _make_mock_db()
        db.execute.return_value = _make_async_result(scalar_return=0)

        channels = await service.list_channels(db)
        assert len(channels) == 4
        channel_map = {c["channel"]: c for c in channels}
        assert "stable" in channel_map
        assert "beta" in channel_map
        assert channel_map["stable"]["release_count"] == 0

    def test_tag_to_channel(self, service: UpdateService) -> None:
        assert service._tag_to_channel("v1.0.0") == ReleaseChannel.STABLE
        assert service._tag_to_channel("v1.1.0-beta.1") == ReleaseChannel.BETA
        assert service._tag_to_channel("nightly-20260726") == ReleaseChannel.NIGHTLY
        assert service._tag_to_channel("v2.0.0-rc.1") == ReleaseChannel.PRE_RELEASE
        assert service._tag_to_channel("v2.0.0-alpha.1") == ReleaseChannel.PRE_RELEASE

    def test_is_newer_version(self, service: UpdateService) -> None:
        assert service._is_newer_version("1.1.0", "1.0.0") is True
        assert service._is_newer_version("2.0.0", "1.9.9") is True
        assert service._is_newer_version("1.0.0", "1.0.0") is False
        assert service._is_newer_version("0.9.9", "1.0.0") is False

    def test_is_security_release(self, service: UpdateService) -> None:
        assert service._is_security_release({"body": "Fix security vulnerability", "name": "Patch"}) is True
        assert service._is_security_release({"body": "Feature release", "name": "New"}) is False

    def test_parse_github_date(self, service: UpdateService) -> None:
        result = service._parse_github_date("2026-07-26T12:00:00Z")
        assert result is not None
        assert result.year == 2026
        assert service._parse_github_date(None) is None

    async def test_verify_checksum_matches(self, service: UpdateService) -> None:
        """SHA256 hash matches."""
        db = _make_mock_db()
        release = _make_release(version="2.0.0", checksum_sha256="abc123hash...")
        db.execute.return_value = _make_async_result(scalar_one_or_none_return=release)

        with (
            patch("builtins.open", MagicMock()) as mock_open,
            patch("hashlib.sha256") as mock_sha,
        ):
            mock_open.return_value.__enter__.return_value.read.return_value = b""
            mock_sha.return_value.hexdigest.return_value = "abc123hash..."
            result = await service.verify_release_integrity(db, "2.0.0", "/fake/path")

        assert result.success is True
        assert "verified" in result.message.lower()

    async def test_verify_checksum_mismatch(self, service: UpdateService) -> None:
        """SHA256 hash mismatch."""
        db = _make_mock_db()
        release = _make_release(version="2.0.0", checksum_sha256="expected_hash")
        db.execute.return_value = _make_async_result(scalar_one_or_none_return=release)

        with (
            patch("builtins.open", MagicMock()) as mock_open,
            patch("hashlib.sha256") as mock_sha,
        ):
            mock_open.return_value.__enter__.return_value.read.return_value = b""
            mock_sha.return_value.hexdigest.return_value = "different_hash"
            result = await service.verify_release_integrity(db, "2.0.0", "/fake/path")

        assert result.success is False
        assert "mismatch" in result.message.lower()

    async def test_verify_checksum_missing_hash(self, service: UpdateService) -> None:
        """No checksum stored for release."""
        db = _make_mock_db()
        release = _make_release(version="2.0.0", checksum_sha256=None)
        db.execute.return_value = _make_async_result(scalar_one_or_none_return=release)
        result = await service.verify_release_integrity(db, "2.0.0", "/fake/path")
        assert result.success is False

    async def test_verify_signature_fallback(self, service: UpdateService) -> None:
        """GPG signature graceful fallback when module unavailable."""
        from core.signature import verify_gpg_signature

        db = _make_mock_db()
        release = _make_release(version="2.0.0")
        db.execute.return_value = _make_async_result(scalar_one_or_none_return=release)
        settings = MagicMock(spec=UpdateSetting)
        settings.gpg_public_key = "fake_key"
        with patch.object(service, "_get_settings", return_value=settings):
            result = await service.verify_digital_signature(db, "2.0.0", "ZmFrZV9zaWc=")
        assert "valid" in result
        assert isinstance(result["valid"], bool)

    async def test_update_public_key(self, service: UpdateService) -> None:
        """Update the GPG public key in settings."""
        db = _make_mock_db()
        settings = MagicMock(spec=UpdateSetting)
        settings.gpg_public_key = None
        settings.channel = ReleaseChannel.STABLE
        settings.schedule = "daily"
        settings.last_check_result = None
        settings.last_update_version = None
        with patch.object(service, "_get_settings", return_value=settings):
            result = await service.update_public_key(db, "new_public_key")
        assert result is not None
        assert settings.gpg_public_key == "new_public_key"


class TestUpdateServiceSync:
    """Test GitHub sync integration."""

    async def test_sync_releases_from_github_success(self, service: UpdateService) -> None:
        db = _make_mock_db()
        db.execute.return_value = _make_async_result(scalar_one_or_none_return=None)

        mock_response = [
            {
                "tag_name": "v1.1.0",
                "name": "Feature Release",
                "body": "New features",
                "draft": False,
                "prerelease": False,
                "published_at": "2026-07-20T12:00:00Z",
                "id": 1001,
                "assets": [
                    {"browser_download_url": "https://example.com/v1.1.0.zip", "size": 1024000},
                ],
            },
        ]

        with patch("services.update_service.httpx.AsyncClient") as mock_client_cls:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = MagicMock(
                status_code=200, json=MagicMock(return_value=mock_response),
            )
            mock_client_cls.return_value.__aenter__.return_value = mock_instance

            count = await service.sync_releases_from_github(db)
            assert count == 1

    async def test_sync_releases_duplicates(self, service: UpdateService) -> None:
        existing = _make_release(version="1.1.0")
        db = _make_mock_db()
        db.execute.return_value = _make_async_result(scalar_one_or_none_return=existing)

        mock_response = [
            {
                "tag_name": "v1.1.0",
                "name": "Feature Release",
                "body": "Same as existing",
                "draft": False,
                "prerelease": False,
                "published_at": "2026-07-20T12:00:00Z",
                "id": 2002,
                "assets": [],
            },
        ]

        with patch("services.update_service.httpx.AsyncClient") as mock_client_cls:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = MagicMock(
                status_code=200, json=MagicMock(return_value=mock_response),
            )
            mock_client_cls.return_value.__aenter__.return_value = mock_instance

            count = await service.sync_releases_from_github(db)
            assert count == 0


@pytest.mark.skip(reason="Needs database integration (DummySession lacks execute)")
class TestUpdateAPI:
    """Test the update API endpoints via ASGI test client."""

    @pytest.fixture
    def client(self, app):
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    async def test_get_version(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/updates/version")
        assert resp.status_code == 200
        data = resp.json()
        assert "current_version" in data

    async def test_check_updates(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/updates/check", params={"channel": "stable"})
        assert resp.status_code == 200

    async def test_check_updates_invalid_channel(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/updates/check", params={"channel": "invalid"})
        assert resp.status_code == 422

    async def test_list_releases(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/updates/releases")
        assert resp.status_code == 200

    async def test_get_release_not_found(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/updates/releases/99.99.99")
        assert resp.status_code == 404

    async def test_get_history(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/updates/history")
        assert resp.status_code == 200

    async def test_get_channels(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/updates/channels")
        assert resp.status_code == 200

    async def test_get_settings(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/updates/settings")
        assert resp.status_code == 200

    async def test_update_settings(self, client: AsyncClient) -> None:
        resp = await client.put("/api/v1/updates/settings", json={"auto_update_enabled": False})
        assert resp.status_code == 200

    async def test_download_release_not_found(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/updates/download/99.99.99")
        assert resp.status_code == 404

    async def test_install_release_not_found(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/updates/install/99.99.99")
        assert resp.status_code == 404

    async def test_rollback_no_history(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/updates/rollback")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False

    async def test_history_status_endpoint(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/updates/history/status/installed")
        assert resp.status_code == 200

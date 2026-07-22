# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Expanded tests for core/config.py — Settings edge cases, validators, properties."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from core.config import Settings, get_settings


class TestSettingsEdgeCases:
    """Edge cases for Settings initialization."""

    def test_database_url_validator_with_postgres_normalized(self):
        s = Settings(database_url="postgres://user:pass@localhost/db", _env_file=None)
        assert s.database_url.startswith("postgresql+asyncpg://")

    def test_database_url_already_asyncpg(self):
        s = Settings(database_url="postgresql+asyncpg://localhost/db", _env_file=None)
        assert s.database_url == "postgresql+asyncpg://localhost/db"

    def test_chatbot_service_url_default(self):
        s = Settings(chatbot_service_url=None, _env_file=None)
        assert "localhost:8010" in s.chatbot_service_url

    def test_chatbot_service_url_normalized(self):
        s = Settings(chatbot_service_url="http://chatbot:8010", _env_file=None)
        assert s.chatbot_service_url.endswith("/api/v1")

    def test_chatbot_service_url_empty_returns_default(self):
        s = Settings(chatbot_service_url="", _env_file=None)
        assert "localhost:8010" in s.chatbot_service_url

    def test_mcp_enabled_in_dev(self):
        s = Settings(environment="development", enable_mcp=True, _env_file=None)
        assert s.mcp_enabled is True

    def test_mcp_disabled_in_production(self):
        s = Settings(environment="production", enable_mcp=True, _env_file=None)
        assert s.mcp_enabled is False

    def test_normalize_openrouteservice_base_url_none(self):
        s = Settings(openrouteservice_base_url=None, _env_file=None)
        assert s.openrouteservice_base_url == "https://api.openrouteservice.org"

    def test_normalize_frontend_url_strips_trailing_slash(self):
        s = Settings(FRONTEND_URL="https://app.example.com/", _env_file=None)
        assert s.frontend_url == "https://app.example.com"

    def test_normalize_frontend_url_none(self):
        s = Settings(FRONTEND_URL=None, _env_file=None)
        assert s.frontend_url is None

    def test_normalize_database_url_raises_on_non_string(self):
        with pytest.raises(ValueError, match="database_url must be a string"):
            Settings(database_url=123, _env_file=None)  # type: ignore[arg-type]

    def test_local_upload_base_url_strips_prefix(self):
        s = Settings(local_upload_base_url="LOCAL_UPLOAD_BASE_URL=http://test.com/uploads", _env_file=None)
        assert s.local_upload_base_url == "http://test.com/uploads"

    def test_emergency_radius_steps_default(self):
        s = Settings(_env_file=None)
        steps = s.emergency_radius_steps
        assert steps[0] == 500
        assert steps[-1] == 50000
        assert len(steps) == 6

    def test_upload_content_types_default(self):
        s = Settings(_env_file=None)
        types = s.allowed_upload_content_types
        assert "image/jpeg" in types
        assert "image/png" in types
        assert "image/webp" in types

    def test_upload_content_types_lowercased(self):
        s = Settings(allowed_upload_content_types_env="IMAGE/JPEG, IMAGE/PNG", _env_file=None)
        assert "image/jpeg" in s.allowed_upload_content_types

    def test_allowed_upload_content_types_empty(self):
        s = Settings(ALLOWED_UPLOAD_CONTENT_TYPES="", _env_file=None)
        # Property returns defaults when env var is empty
        assert len(s.allowed_upload_content_types) == 3
        assert "image/jpeg" in s.allowed_upload_content_types


class TestGetSettings:
    """Tests for get_settings singleton."""

    def test_get_settings_caches(self):
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_get_settings_has_required_fields(self):
        s = get_settings()
        assert hasattr(s, "app_name")
        assert hasattr(s, "database_url")
        assert hasattr(s, "environment")

    def test_get_settings_creates_dirs(self):
        with patch("core.config.Path.mkdir") as mock_mkdir:
            get_settings.cache_clear()
            s = get_settings()
            assert mock_mkdir.called

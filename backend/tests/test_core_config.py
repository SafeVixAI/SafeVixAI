# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from core.config import Settings, get_settings


class TestSettingsCorsOrigins:
    _KWARGS = {"_env_file": None}

    def test_star_default(self):
        s = Settings(**self._KWARGS)
        assert s.cors_origins == ["*"]

    def test_empty_string(self):
        s = Settings(**self._KWARGS, CORS_ORIGINS="")
        assert s.cors_origins == ["*"]

    def test_comma_separated(self):
        s = Settings(**self._KWARGS, CORS_ORIGINS="http://a.com, https://b.com")
        assert s.cors_origins == ["http://a.com", "https://b.com"]

    def test_comma_separated_with_spaces(self):
        s = Settings(**self._KWARGS, CORS_ORIGINS="http://a.com , https://b.com ")
        assert s.cors_origins == ["http://a.com", "https://b.com"]

    def test_single_origin(self):
        s = Settings(**self._KWARGS, CORS_ORIGINS="http://localhost:3000")
        assert s.cors_origins == ["http://localhost:3000"]

    def test_production_star_warning(self, caplog):
        caplog.set_level("WARNING")
        s = Settings(**self._KWARGS, CORS_ORIGINS="*", environment="production")
        assert s.cors_origins == ["*"]
        assert any("CORS_ORIGINS=* in production" in msg for msg in caplog.messages)


class TestSettingsEmergencyRadiusSteps:
    _KWARGS = {"_env_file": None}

    def test_default(self):
        s = Settings(**self._KWARGS)
        assert s.emergency_radius_steps == [500, 1000, 5000, 10000, 25000, 50000]

    def test_custom(self):
        s = Settings(**self._KWARGS, EMERGENCY_RADIUS_STEPS="100,200,300")
        assert s.emergency_radius_steps == [100, 200, 300]

    def test_with_spaces(self):
        s = Settings(**self._KWARGS, EMERGENCY_RADIUS_STEPS="100, 200, 300")
        assert s.emergency_radius_steps == [100, 200, 300]

    def test_single_step(self):
        s = Settings(**self._KWARGS, EMERGENCY_RADIUS_STEPS="5000")
        assert s.emergency_radius_steps == [5000]


class TestSettingsOverpassUrls:
    _KWARGS = {"_env_file": None}

    def test_default_fallback(self):
        s = Settings(**self._KWARGS)
        assert s.overpass_urls == [s.overpass_url]

    def test_none_env(self):
        s = Settings(**self._KWARGS, OVERPASS_URLS=None)
        assert s.overpass_urls == [s.overpass_url]

    def test_empty_env(self):
        s = Settings(**self._KWARGS, OVERPASS_URLS="")
        assert s.overpass_urls == [s.overpass_url]

    def test_multiple_urls(self):
        s = Settings(**self._KWARGS, OVERPASS_URLS="https://a.example/api,https://b.example/api")
        assert s.overpass_urls == ["https://a.example/api", "https://b.example/api"]


class TestSettingsAllowedUploadContentTypes:
    _KWARGS = {"_env_file": None}

    def test_default(self):
        s = Settings(**self._KWARGS)
        assert "image/jpeg" in s.allowed_upload_content_types

    def test_custom(self):
        s = Settings(**self._KWARGS, ALLOWED_UPLOAD_CONTENT_TYPES="application/pdf,text/plain")
        assert s.allowed_upload_content_types == ["application/pdf", "text/plain"]

    def test_case_insensitive(self):
        s = Settings(**self._KWARGS, ALLOWED_UPLOAD_CONTENT_TYPES="IMAGE/JPEG, application/PDF")
        assert s.allowed_upload_content_types == ["image/jpeg", "application/pdf"]

    def test_empty_fallback(self):
        s = Settings(**self._KWARGS, ALLOWED_UPLOAD_CONTENT_TYPES="")
        assert s.allowed_upload_content_types == ["image/jpeg", "image/png", "image/webp"]


class TestSettingsNormalizeUploadBaseUrl:
    _KWARGS = {"_env_file": None}

    def test_none(self):
        s = Settings(**self._KWARGS, local_upload_base_url=None)
        assert s.local_upload_base_url is None

    def test_strips_trailing_slash(self):
        s = Settings(**self._KWARGS, local_upload_base_url="http://localhost:8000/uploads/")
        assert s.local_upload_base_url == "http://localhost:8000/uploads"

    def test_handles_env_prefix(self):
        s = Settings(**self._KWARGS, local_upload_base_url="LOCAL_UPLOAD_BASE_URL=http://localhost:8000/uploads")
        assert s.local_upload_base_url == "http://localhost:8000/uploads"

    def test_empty_string_is_none(self):
        s = Settings(**self._KWARGS, local_upload_base_url="")
        assert s.local_upload_base_url is None

    def test_not_a_string_raises(self):
        with pytest.raises(ValueError, match="must be a string"):
            Settings(**self._KWARGS, local_upload_base_url=123)


class TestSettingsNormalizeChatbotServiceUrl:
    _KWARGS = {"_env_file": None}

    def test_default(self):
        s = Settings(**self._KWARGS)
        assert s.chatbot_service_url == "http://localhost:8010/api/v1"

    def test_none(self):
        s = Settings(**self._KWARGS, chatbot_service_url=None)
        assert s.chatbot_service_url == "http://localhost:8010/api/v1"

    def test_empty_string(self):
        s = Settings(**self._KWARGS, chatbot_service_url="")
        assert s.chatbot_service_url == "http://localhost:8010/api/v1"

    def test_already_has_suffix(self):
        s = Settings(**self._KWARGS, chatbot_service_url="http://example.com/api/v1")
        assert s.chatbot_service_url == "http://example.com/api/v1"

    def test_strips_trailing_slash(self):
        s = Settings(**self._KWARGS, chatbot_service_url="http://example.com/")
        assert s.chatbot_service_url == "http://example.com/api/v1"

    def test_appends_api_v1(self):
        s = Settings(**self._KWARGS, chatbot_service_url="http://example.com")
        assert s.chatbot_service_url == "http://example.com/api/v1"

    def test_not_a_string_raises(self):
        with pytest.raises(ValueError, match="must be a string"):
            Settings(**self._KWARGS, chatbot_service_url=456)


class TestSettingsNormalizeFrontendUrl:
    _KWARGS = {"_env_file": None}

    def test_default(self):
        s = Settings(**self._KWARGS)
        assert s.frontend_url is None

    def test_none(self):
        s = Settings(**self._KWARGS, FRONTEND_URL=None)
        assert s.frontend_url is None

    def test_empty_string(self):
        s = Settings(**self._KWARGS, FRONTEND_URL="")
        assert s.frontend_url is None

    def test_strips_trailing_slash(self):
        s = Settings(**self._KWARGS, FRONTEND_URL="http://localhost:3000/")
        assert s.frontend_url == "http://localhost:3000"

    def test_valid_url(self):
        s = Settings(**self._KWARGS, FRONTEND_URL="https://safevixai.vercel.app")
        assert s.frontend_url == "https://safevixai.vercel.app"

    def test_not_a_string_raises(self):
        with pytest.raises(ValueError, match="must be a string"):
            Settings(**self._KWARGS, FRONTEND_URL=789)


class TestSettingsGetSettings:
    def test_cached_return(self):
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_cache_cleared(self):
        get_settings.cache_clear()
        s1 = get_settings()
        get_settings.cache_clear()
        s2 = get_settings()
        assert s1 is not s2

    def test_production_cors_star_raises(self):
        get_settings.cache_clear()
        with patch("core.config.Settings") as MockSettings:
            mock = MagicMock()
            mock.environment = "production"
            mock.cors_origins_env = "*"
            MockSettings.return_value = mock
            with pytest.raises(RuntimeError, match="CORS_ORIGINS must list explicit origins"):
                get_settings()


class TestSettingsMcpEnabled:
    _KWARGS = {"_env_file": None}

    def test_disabled_in_production(self):
        s = Settings(**self._KWARGS, enable_mcp=True, environment="production")
        assert s.mcp_enabled is False

    def test_enabled_in_development(self):
        s = Settings(**self._KWARGS, enable_mcp=True, environment="development")
        assert s.mcp_enabled is True

    def test_enabled_in_test(self):
        s = Settings(**self._KWARGS, enable_mcp=True, environment="test")
        assert s.mcp_enabled is True

    def test_enabled_by_env_in_development(self):
        s = Settings(**self._KWARGS, enable_mcp=False, environment="development")
        assert s.mcp_enabled is True

    def test_disabled_when_not_set_and_production(self):
        s = Settings(**self._KWARGS, enable_mcp=False, environment="production")
        assert s.mcp_enabled is False


class TestSettingsNormalizeOpenrouteserviceUrl:
    _KWARGS = {"_env_file": None}

    def test_default(self):
        s = Settings(**self._KWARGS)
        assert s.openrouteservice_base_url == "https://api.openrouteservice.org"

    def test_none(self):
        s = Settings(**self._KWARGS, openrouteservice_base_url=None)
        assert s.openrouteservice_base_url == "https://api.openrouteservice.org"

    def test_strips_trailing_slash(self):
        s = Settings(**self._KWARGS, openrouteservice_base_url="https://api.ors.example/")
        assert s.openrouteservice_base_url == "https://api.ors.example"

    def test_empty_string(self):
        s = Settings(**self._KWARGS, openrouteservice_base_url="")
        assert s.openrouteservice_base_url == "https://api.openrouteservice.org"

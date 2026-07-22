# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Module-level reload tests for core/limiter.py.

Covers code paths that execute at module import time:
- Line 18: Limiter with storage_uri (settings.redis_url is set)
- Line 21: limiter.enabled = False (settings.environment == "test")

Uses sys.modules manipulation + importlib.import_module to force
a fresh import under patch, avoiding importlib.reload() issues.
"""

from __future__ import annotations

import importlib
import sys
from unittest.mock import MagicMock, patch


def teardown_module(module):
    """Restore core.limiter to original state after all tests."""
    if "core.limiter" in sys.modules:
        del sys.modules["core.limiter"]
    importlib.import_module("core.limiter")


class TestLimiterModuleLevelRedisUrl:
    """Tests for module-level limiter creation with redis_url set."""

    def _fresh_limiter_import(self, settings_mock):
        """Import core.limiter fresh under patch, returns the module.

        Patches at the SOURCE (core.config.get_settings and slowapi.Limiter)
        so the module-level 'from core.config import get_settings' and
        'from slowapi import Limiter' statements pick up the mocks.
        """
        key = "core.limiter"
        if key in sys.modules:
            del sys.modules[key]
        with patch("core.config.get_settings", return_value=settings_mock), \
             patch("slowapi.Limiter") as mock_class:
            mod = importlib.import_module(key)
            return mod, mock_class

    def test_limiter_created_with_redis_url(self):
        """When redis_url is set, limiter should use storage_uri (line 18)."""
        settings = MagicMock()
        settings.redis_url = "redis://localhost:6379/0"
        settings.environment = "development"

        mod, mock_class = self._fresh_limiter_import(settings)
        mock_class.assert_called_once()
        _, kwargs = mock_class.call_args
        assert "storage_uri" in kwargs
        assert kwargs["storage_uri"] == "redis://localhost:6379/0"

    def test_limiter_created_without_redis(self):
        """Without redis_url, limiter should not use storage_uri (line 21 fallback)."""
        settings = MagicMock()
        settings.redis_url = None
        settings.environment = "development"

        mod, mock_class = self._fresh_limiter_import(settings)
        mock_class.assert_called_once()
        _, kwargs = mock_class.call_args
        assert "storage_uri" not in kwargs

    def test_limiter_disabled_in_test_env(self):
        """In test environment, limiter.enabled should be False (line 21)."""
        settings = MagicMock()
        settings.redis_url = None
        settings.environment = "test"

        mod, mock_class = self._fresh_limiter_import(settings)
        mock_instance = mock_class.return_value
        assert mock_instance.enabled is False

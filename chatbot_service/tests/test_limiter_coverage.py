# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch


class TestLimiterSlowapi:
    def test_limiter_has_limit(self):
        import limiter
        assert hasattr(limiter.limiter, 'limit')

    def test_limiter_limit_passthrough(self):
        import limiter
        decorator = limiter.limiter.limit("10/minute")
        assert callable(decorator)


class TestLimiterNoopFallback:
    def test_noop_fallback_when_slowapi_missing(self):
        if 'limiter' in sys.modules:
            del sys.modules['limiter']
        with patch.dict(sys.modules, {'slowapi': None}):
            import importlib
            mod = importlib.import_module('limiter')
            importlib.reload(mod)
            assert hasattr(mod.limiter, 'limit')
            decorator = mod.limiter.limit("5/minute")
            wrapped = decorator(lambda: 42)
            assert wrapped() == 42

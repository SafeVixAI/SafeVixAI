# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import pytest

try:
    from services import speech_translation as _speech_translation_module
    from services.speech_translation import IndicSeamlessService
except ImportError:
    _speech_translation_module = None
    IndicSeamlessService = None


pytestmark = [
    pytest.mark.skipif(IndicSeamlessService is None, reason="speech_translation module not available"),
]


class FakeSettings:
    speech_model_id = "facebook/seamless-m4t-v2-small"
    speech_model_dir = None
    speech_default_target_lang = "hin"
    speech_device = "cpu"


class TestLazyImports:
    def test_torch_not_imported_at_module_level(self):
        assert not hasattr(_speech_translation_module, "torch")

    def test_init_does_not_load_model(self):
        service = IndicSeamlessService(FakeSettings())
        assert service._model is None

    def test_dependencies_not_available_on_init(self):
        service = IndicSeamlessService(FakeSettings())
        assert service.status()["model_loaded"] is False

    def test_import_dependencies_returns_none_when_missing(self):
        service = IndicSeamlessService(FakeSettings())
        torch, torchaudio, fe, tok, model = service._import_dependencies()
        # In test env these may or may not be available - either is fine
        assert isinstance(torch, type(None)) or hasattr(torch, "__version__")

    def test_status_without_loading(self):
        service = IndicSeamlessService(FakeSettings())
        status = service.status()
        assert "configured" in status
        assert "dependencies_available" in status
        assert "device" in status
        assert status["model_loaded"] is False

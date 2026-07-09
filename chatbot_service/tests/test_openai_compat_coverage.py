# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

from providers.openai_compat import OpenAICompatibleProvider


class TestOpenAICompatibleProvider:
    def test_default_constructor(self):
        p = OpenAICompatibleProvider()
        assert p.api_key_env() == ""
        assert p.default_model() == "llama3.2"

    def test_base_url_default(self):
        p = OpenAICompatibleProvider()
        assert "11434" in p.base_url()

    def test_base_url_custom(self):
        p = OpenAICompatibleProvider(base_url="http://custom:8080")
        assert "custom:8080" in p.base_url()

    def test_name_property_with_display_name(self):
        p = OpenAICompatibleProvider(display_name="My Test Provider")
        assert p.name == "my-test-provider"

    def test_name_property_empty_display_name(self):
        p = OpenAICompatibleProvider(display_name="")
        p.name = "custom"
        # name setter is a no-op, so name is still the default
        assert p.name == "custom"

    def test_name_setter_is_noop(self):
        p = OpenAICompatibleProvider(display_name="original")
        p.name = "overridden"
        assert p.name == "original"

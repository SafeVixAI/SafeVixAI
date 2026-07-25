# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from utils.token_guard import (
    MAX_SAFE_INPUT_TOKENS,
    SYSTEM_PROMPT_FINGERPRINT,
    estimate_messages_tokens,
    estimate_tokens,
    sanitize_output,
    should_skip_groq,
    trim_history,
)


class TestEstimateTokens:
    def test_empty_text(self):
        assert estimate_tokens("") == 0

    def test_none_text(self):
        assert estimate_tokens(None) == 0

    def test_short_text(self):
        assert estimate_tokens("hello world") == 2

    def test_long_text(self):
        assert estimate_tokens("a" * 100) == 25


class TestEstimateMessagesTokens:
    def test_empty_messages(self):
        assert estimate_messages_tokens([]) == 0

    def test_single_message(self):
        messages = [{"role": "user", "content": "hello world"}]
        assert estimate_messages_tokens(messages) == 2

    def test_multiple_messages(self):
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]
        assert estimate_messages_tokens(messages) == 3

    def test_missing_content_key(self):
        messages = [{"role": "user"}]
        assert estimate_messages_tokens(messages) == 0

    def test_none_content(self):
        messages = [{"role": "user", "content": None}]
        assert estimate_messages_tokens(messages) == 0


class TestTrimHistory:
    def test_under_max_returns_unchanged(self):
        messages = [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}]
        result = trim_history(messages)
        assert len(result) == 2

    def test_over_max_trims(self, monkeypatch):
        monkeypatch.setattr("utils.token_guard.MAX_HISTORY_TOKENS", 2)
        messages = [
            {"role": "system", "content": "sys msg"},
            {"role": "user", "content": "msg1"},
            {"role": "assistant", "content": "msg2"},
            {"role": "user", "content": "msg3"},
        ]
        result = trim_history(messages, max_tokens=2)
        assert len(result) < 4
        assert result[0]["role"] == "system"

    def test_preserves_first_message(self):
        messages = [
            {"role": "system", "content": "x" * 100},
            {"role": "user", "content": "y" * 100},
            {"role": "assistant", "content": "z" * 100},
        ]
        result = trim_history(messages, max_tokens=10)
        assert result[0] == messages[0]

    def test_exact_max_returns_unchanged(self):
        messages = [{"role": "user", "content": "a"}]
        result = trim_history(messages, max_tokens=100)
        assert result == messages


class TestShouldSkipGroq:
    def test_below_max_returns_false(self):
        msg = [{"role": "user", "content": "short"}]
        assert should_skip_groq(msg) is False

    def test_above_max_returns_true(self):
        msg = [{"role": "user", "content": "x" * (MAX_SAFE_INPUT_TOKENS * 4 + 10)}]
        assert should_skip_groq(msg) is True


class TestSanitizeOutput:
    def test_very_short_response_unchanged(self):
        assert sanitize_output("short") == "short"

    def test_system_prompt_leak_redacted(self):
        result = sanitize_output(f"Some text {SYSTEM_PROMPT_FINGERPRINT} more text")
        assert "I cannot reveal" in result
        assert "road safety" in result

    def test_case_insensitive_detection(self):
        result = sanitize_output(f"Some text {SYSTEM_PROMPT_FINGERPRINT.lower()} in it")
        assert "I cannot reveal" in result

    def test_normal_response_unchanged(self):
        text = "This is a normal road safety response without any prompt info."
        assert sanitize_output(text) == text

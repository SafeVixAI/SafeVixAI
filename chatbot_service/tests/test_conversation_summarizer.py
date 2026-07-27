# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import pytest

from memory.summarizer import ConversationSummarizer


class TestConversationSummarizer:
    def test_should_not_summarize_empty(self) -> None:
        cs = ConversationSummarizer(threshold=8)
        assert cs.should_summarize([]) is False

    def test_should_not_summarize_below_threshold(self) -> None:
        cs = ConversationSummarizer(threshold=8)
        assert cs.should_summarize([{"role": "user", "content": "hi"}] * 7) is False

    def test_should_summarize_at_threshold(self) -> None:
        cs = ConversationSummarizer(threshold=8)
        assert cs.should_summarize([{"role": "user", "content": "hi"}] * 8) is True

    def test_should_summarize_above_threshold(self) -> None:
        cs = ConversationSummarizer(threshold=8)
        assert cs.should_summarize([{"role": "user", "content": "hi"}] * 10) is True

    def test_summarize_empty_history(self) -> None:
        cs = ConversationSummarizer()
        result = cs.summarize([])
        assert result["summary"] == ""
        assert result["turn_count"] == 0

    def test_summarize_simple_conversation(self) -> None:
        cs = ConversationSummarizer()
        history = [
            {"role": "user", "content": "What is the fine for speeding?"},
            {"role": "assistant", "content": "The fine for speeding is Rs. 1000."},
            {"role": "user", "content": "Where is the nearest hospital?"},
        ]
        result = cs.summarize(history)
        assert result["turn_count"] == 3
        assert result["user_message_count"] == 2
        assert result["assistant_message_count"] == 1

    def test_summarize_extracts_keywords(self) -> None:
        cs = ConversationSummarizer()
        history = [
            {"role": "user", "content": "I was in an accident near the hospital"},
            {"role": "assistant", "content": "Call 112 immediately for emergency services"},
        ]
        result = cs.summarize(history)
        assert "accident" in result["topics"] or "hospital" in result["topics"] or "emergency" in result["topics"]

    def test_summarize_with_intents(self) -> None:
        cs = ConversationSummarizer()
        history = [
            {"role": "user", "content": "challan question", "metadata": {"intent": "challan"}},
            {"role": "assistant", "content": "here is the fine info", "metadata": {"intent": "challan"}},
        ]
        result = cs.summarize(history)
        assert "challan" in result["intents"]

    def test_summarize_with_mixed_metadata(self) -> None:
        cs = ConversationSummarizer()
        history = [
            {"role": "user", "content": "hi", "metadata": "not_a_dict"},
            {"role": "assistant", "content": "hello"},
        ]
        result = cs.summarize(history)
        assert result["turn_count"] == 2

    def test_summarize_truncates_long_messages(self) -> None:
        cs = ConversationSummarizer()
        long_msg = "word " * 500
        history = [{"role": "user", "content": long_msg}]
        result = cs.summarize(history)
        assert result["turn_count"] == 1

    def test_get_summary_for_history_below_threshold(self) -> None:
        cs = ConversationSummarizer(threshold=8)
        history = [{"role": "user", "content": "hi"}] * 3
        result, summary = cs.get_summary_for_history(history)
        assert len(result) == 3
        assert summary is None

    def test_get_summary_for_history_at_threshold(self) -> None:
        cs = ConversationSummarizer(threshold=4)
        history = [{"role": "user", "content": f"msg{i}"} for i in range(5)]
        result, summary = cs.get_summary_for_history(history)
        assert summary is not None
        assert result[0]["role"] == "system"
        assert "[Conversation summary:" in result[0]["content"]

    def test_extract_topics_identifies_keywords(self) -> None:
        topics = ConversationSummarizer._extract_topics(["There was an accident on the highway"])
        assert "accident" in topics

    def test_extract_topics_empty_list(self) -> None:
        topics = ConversationSummarizer._extract_topics([])
        assert topics == set()

    def test_extract_topics_multiple_keywords(self) -> None:
        topics = ConversationSummarizer._extract_topics([
            "I got a challan for not wearing a helmet",
            "The weather is rainy and foggy",
        ])
        assert "challan" in topics
        assert "helmet" in topics
        assert "rain" in topics or "fog" in topics

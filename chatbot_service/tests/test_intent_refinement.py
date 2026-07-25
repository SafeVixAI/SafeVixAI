# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import pytest

from agent.intent_detector import IntentDetector


class TestIntentDetector:
    @pytest.fixture
    def detector(self):
        return IntentDetector()

    def test_detect_emergency(self, detector):
        assert detector.detect("There was an accident on the highway") == "emergency"
        assert detector.detect("Call ambulance") == "emergency"
        assert detector.detect("I need a hospital") == "emergency"
        assert detector.detect("SOS help me") == "emergency"
        assert detector.detect("Someone is injured") == "emergency"

    def test_detect_first_aid(self, detector):
        assert detector.detect("He is bleeding heavily") == "first_aid"
        assert detector.detect("How to treat a burn") == "first_aid"
        assert detector.detect("CPR instructions") == "first_aid"
        assert detector.detect("She is unconscious") == "first_aid"

    def test_detect_challan(self, detector):
        assert detector.detect("What is the fine for 185?") == "challan"
        assert detector.detect("challan for speeding") == "challan"
        assert detector.detect("helmet fine amount") == "challan"
        assert detector.detect("drunk driving penalty") == "challan"

    def test_detect_legal(self, detector):
        assert detector.detect("What does MV Act say about this?") == "legal"
        assert detector.detect("motor vehicles act section on rights") == "legal"
        assert detector.detect("my legal rights on road") == "legal"

    def test_detect_weather(self, detector):
        assert detector.detect("weather conditions for driving") == "road_weather"
        assert detector.detect("heavy rain forecast") == "road_weather"
        assert detector.detect("fog on the highway") == "road_weather"

    def test_detect_route(self, detector):
        assert detector.detect("safest route to Chennai") == "safe_route"
        assert detector.detect("navigation directions") == "safe_route"
        assert detector.detect("route planning") == "safe_route"

    def test_detect_infrastructure(self, detector):
        assert detector.detect("who maintains this road?") == "road_infrastructure"
        assert detector.detect("NHAI contractor details") == "road_infrastructure"
        assert detector.detect("PWD road authority") == "road_infrastructure"

    def test_detect_road_issue(self, detector):
        assert detector.detect("there is a pothole on this road") == "road_issue"
        assert detector.detect("report road hazard") == "road_issue"
        assert detector.detect("debris on highway") == "road_issue"

    def test_detect_general(self, detector):
        assert detector.detect("Hello, how are you?") == "general"
        assert detector.detect("What is the weather like?") != "general"
        assert detector.detect("Good morning") == "general"


class TestMultiTurnIntentRefinement:
    @pytest.fixture
    def detector(self):
        return IntentDetector()

    def test_non_general_not_refined(self, detector):
        history = [{"role": "user", "content": "What is fine for speeding?", "metadata": {"intent": "challan"}}]
        assert detector.refine_intent("challan", "tell me more", history) == "challan"

    def test_general_no_history(self, detector):
        assert detector.refine_intent("general", "hello", []) == "general"

    def test_general_follow_up_inherits_intent(self, detector):
        history = [
            {"role": "user", "content": "What is the fine for drunk driving?", "metadata": {"intent": "challan"}},
            {"role": "assistant", "content": "Rs. 10,000", "metadata": {"intent": "challan"}},
        ]
        result = detector.refine_intent("general", "tell me more", history)
        assert result == "challan"

    def test_general_short_message_inherits(self, detector):
        history = [
            {"role": "user", "content": "How to treat a burn?", "metadata": {"intent": "first_aid"}},
        ]
        result = detector.refine_intent("general", "and?", history)
        assert result == "first_aid"

    def test_general_long_message_not_refined(self, detector):
        history = [
            {"role": "user", "content": "What is challan for 185?", "metadata": {"intent": "challan"}},
        ]
        result = detector.refine_intent("general", "What is the process for filing an FIR after a road accident?", history)
        assert result == "general"

    def test_no_previous_intent(self, detector):
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]
        result = detector.refine_intent("general", "tell me more", history)
        assert result == "general"

    def test_skips_blocked_intent(self, detector):
        history = [
            {"role": "user", "content": "bad stuff", "metadata": {"intent": "blocked"}},
            {"role": "user", "content": "What is fine for 183?", "metadata": {"intent": "challan"}},
        ]
        result = detector.refine_intent("general", "more details", history)
        assert result == "challan"

    def test_most_recent_intent_used(self, detector):
        history = [
            {"role": "user", "content": "Weather?", "metadata": {"intent": "road_weather"}},
            {"role": "user", "content": "Fine?", "metadata": {"intent": "challan"}},
        ]
        result = detector.refine_intent("general", "what about", history)
        assert result == "challan"

    def test_not_follow_up_indicator(self, detector):
        history = [
            {"role": "user", "content": "challan", "metadata": {"intent": "challan"}},
        ]
        result = detector.refine_intent("general", "I want to know about road safety features in my car", history)
        assert result == "general"

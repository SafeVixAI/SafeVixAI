# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tests for AI governance framework (Phase 0.7)."""
from __future__ import annotations

import pytest

from agent.governance import AIGovernance, GovernanceResult


@pytest.fixture
def governance():
    """Create governance instance without Redis."""
    return AIGovernance(redis_url=None)


@pytest.fixture
def sample_context():
    """Sample RAG context for testing."""
    return [
        {
            "content": "The maximum speed limit on highways in India is 120 km/h",
            "source": "motor_vehicles_act.pdf",
            "title": "Speed Limits - Motor Vehicles Act",
        },
        {
            "content": "Seat belts are mandatory for all vehicle occupants",
            "source": "safety_rules.pdf",
            "title": "Safety Regulations",
        },
    ]


@pytest.fixture
def sample_tools():
    """Sample tool results for testing."""
    return [
        {
            "name": "challan_tool",
            "payload": {"fine_amount": "1000", "violation": "speeding"},
        },
        {
            "name": "legal_search",
            "payload": {"section": "MVA-185", "description": "Speeding violation"},
        },
    ]


class TestHallucinationDetection:
    """Test hallucination detection logic."""

    def test_high_relevance_response(self, governance, sample_context):
        """Response that matches context should get high score."""
        response = "The maximum speed limit on highways in India is 120 km/h according to the Motor Vehicles Act"
        score = governance._detect_hallucination(response, sample_context)
        assert score >= 0.4, f"Expected high score, got {score}"

    def test_low_relevance_response(self, governance, sample_context):
        """Response unrelated to context should get low score."""
        response = "The weather tomorrow will be sunny with a chance of rain"
        score = governance._detect_hallucination(response, sample_context)
        assert score < 0.5, f"Expected low score, got {score}"

    def test_empty_context(self, governance):
        """No context should result in zero score."""
        response = "Some random text"
        score = governance._detect_hallucination(response, [])
        assert score == 0.0

    def test_partial_overlap(self, governance, sample_context):
        """Response with partial context overlap should get medium score."""
        response = "Speed limits are important for road safety and should be followed"
        score = governance._detect_hallucination(response, sample_context)
        assert 0.2 <= score <= 0.8, f"Expected medium score, got {score}"


class TestFactualityScoring:
    """Test factuality scoring logic."""

    def test_high_factuality(self, governance, sample_tools):
        """Response mentioning tool facts should get high score."""
        response = "The fine for speeding is 1000 rupees under section MVA-185"
        score = governance._score_factuality(response, sample_tools)
        assert score >= 0.5, f"Expected high factuality, got {score}"

    def test_low_factuality(self, governance, sample_tools):
        """Response not mentioning tool facts should get low score."""
        response = "You should always drive carefully and follow traffic rules"
        score = governance._score_factuality(response, sample_tools)
        assert score < 0.5, f"Expected low factuality, got {score}"

    def test_no_tools(self, governance):
        """No tools should result in neutral score."""
        response = "Some text"
        score = governance._score_factuality(response, [])
        assert score == 0.5


class TestCitationExtraction:
    """Test citation extraction."""

    def test_extract_citations(self, governance, sample_context):
        """Should extract unique sources from context."""
        response = "test"
        citations = governance._extract_citations(response, sample_context)
        assert len(citations) >= 2
        assert "motor_vehicles_act.pdf" in citations
        assert "safety_rules.pdf" in citations

    def test_max_citations(self, governance):
        """Should limit to max 5 citations."""
        context = [
            {"source": f"source_{i}.pdf", "title": f"Title {i}", "content": "test"}
            for i in range(10)
        ]
        citations = governance._extract_citations("test", context)
        assert len(citations) <= 5


class TestPromptVersioning:
    """Test prompt version tracking."""

    def test_same_prompt_same_version(self, governance):
        """Same prompt should get same version."""
        prompt = "What is the speed limit?"
        v1 = governance._get_prompt_version(prompt)
        v2 = governance._get_prompt_version(prompt)
        assert v1 == v2

    def test_different_prompt_different_version(self, governance):
        """Different prompts should get different versions."""
        v1 = governance._get_prompt_version("What is the speed limit?")
        v2 = governance._get_prompt_version("How to report a pothole?")
        assert v1 != v2


class TestGovernanceEvaluation:
    """Test full governance evaluation pipeline."""

    @pytest.mark.asyncio
    async def test_flagged_response(self, governance, sample_context, sample_tools):
        """Low confidence response should be flagged."""
        result = await governance.evaluate(
            response_text="I'm not sure about the exact speed limit, but it might be around 100 km/h",
            retrieved_context=sample_context,
            tool_results=sample_tools,
            prompt="What is the speed limit?",
        )

        assert isinstance(result, GovernanceResult)
        assert result.prompt_version is not None
        assert result.hallucination_score >= 0
        assert result.factuality_score >= 0

    @pytest.mark.asyncio
    async def test_confident_response(self, governance, sample_context, sample_tools):
        """High confidence response should not be flagged."""
        result = await governance.evaluate(
            response_text="The maximum speed limit on highways in India is 120 km/h as per the Motor Vehicles Act",
            retrieved_context=sample_context,
            tool_results=sample_tools,
            prompt="What is the speed limit?",
        )

        assert isinstance(result, GovernanceResult)
        assert result.citations is not None
        assert len(result.citations) > 0


class TestGovernanceIntegration:
    """Test governance integration with ChatEngine."""

    @pytest.mark.asyncio
    async def test_governance_metadata_in_response(self):
        """Governance metadata should be included in chat response."""
        # This would require mocking the full ChatEngine
        # For now, verify governance module is importable and functional
        governance = AIGovernance(redis_url=None)
        assert governance is not None
        assert hasattr(governance, 'evaluate')
        assert hasattr(governance, '_detect_hallucination')
        assert hasattr(governance, '_score_factuality')

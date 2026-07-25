# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

from unittest.mock import patch

import pytest

from agent.intent_detector import INTENT_CLASSES, IntentDetector
from rag.embeddings import build_embedding_function


@pytest.fixture(autouse=True)
def mock_embeddings():
    with patch('agent.intent_detector.build_embedding_function') as mock_build:
        # Return a deterministic hash embedding function that acts locally
        mock_build.return_value = build_embedding_function('hash')
        yield

def test_intent_detector_routes_emergency_queries():
    detector = IntentDetector()
    assert detector.detect('Need an ambulance after an accident') == 'emergency'


def test_intent_detector_routes_challan_queries():
    detector = IntentDetector()
    assert detector.detect('What is the fine under section 185 in TN?') == 'challan'


def test_intent_detector_covers_all_supported_classes():
    detector = IntentDetector()

    examples = {
        'emergency': 'SOS, police and ambulance needed after crash',
        'first_aid': 'First aid for bleeding wound',
        'challan': 'Helmet fine amount in Chennai',
        'legal': 'Explain MV Act inspection rights',
        'road_issue': 'Report road hazard debris on the flyover',
        'road_weather': 'Is fog or rain making the highway unsafe?',
        'safe_route': 'Find the safest route to the office',
        'road_infrastructure': 'Who maintains this PMGSY road authority?',
        'general': 'How should I prepare for a long road trip?',
    }

    assert tuple(examples) == INTENT_CLASSES
    for expected, message in examples.items():
        assert detector.detect(message) == expected

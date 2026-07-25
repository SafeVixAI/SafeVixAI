# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import json
from pathlib import Path

from config import get_settings
from tools.first_aid_tool import FirstAidTool


def test_first_aid_tool_loads_guides_from_seed_file():
    tool = FirstAidTool(get_settings())
    guide = tool.lookup('How do I help with severe burns?')

    assert guide is not None, "Guide should not be None"
    assert guide['title'] == 'Burns'
    assert guide['steps']


def test_first_aid_tool_supports_article_array_format(tmp_path: Path):
    payload = [
        {
            'id': 'burns_chemical',
            'title': 'Chemical Burns',
            'category': 'burns',
            'steps': ['Flush the area with running water.', 'Remove contaminated clothing carefully.'],
            'warning': 'Do not apply neutralizing chemicals.',
            'call_ambulance_if': ['The burn involves the face or difficulty breathing.'],
        }
    ]
    (tmp_path / 'first_aid.json').write_text(json.dumps(payload), encoding='utf-8')
    settings = get_settings().model_copy(update={"rag_data_dir": tmp_path})

    tool = FirstAidTool(settings)
    guide = tool.lookup('How do I help someone with chemical burns?')

    assert guide is not None
    assert guide['title'] == 'Chemical Burns'
    assert guide['category'] == 'burns'
    assert guide['call_ambulance_if']

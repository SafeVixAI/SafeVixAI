# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from prompts import reload, get_system_prompt, get_prohibited_patterns
from prompts import get_harm_patterns, get_jailbreak_patterns
from prompts import get_severe_output_patterns, get_medical_keywords
from prompts import get_medical_disclaimer, get_sub_agent_prompt
from prompts import get_episodic_memory_prompt, get_max_history
from prompts import get_max_response_tokens


_SAMPLE_YAML = """
system_prompt: "Test system prompt"
prohibited_patterns:
  - "test pattern 1"
  - "test pattern 2"
harm_patterns:
  - "harm pattern 1"
jailbreak_patterns:
  - "jailbreak pattern 1"
severe_output_patterns:
  - "severe output 1"
medical_keywords:
  - "test medical"
medical_disclaimer: "Test disclaimer."
sub_agent_prompts:
  legal: "Legal sub-agent test"
  first_aid: "First aid sub-agent test"
episodic_memory_extraction_prompt: "Extract from: {history_text}"
max_history: 5
max_response_tokens: 400
"""


class TestPromptsLoader:
    def _write_yaml(self, content: str) -> Path:
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8')
        tmp.write(content)
        tmp.close()
        return Path(tmp.name)

    def test_get_system_prompt(self):
        tmp = self._write_yaml(_SAMPLE_YAML)
        reload(str(tmp))
        assert get_system_prompt() == "Test system prompt"

    def test_get_prohibited_patterns(self):
        tmp = self._write_yaml(_SAMPLE_YAML)
        reload(str(tmp))
        patterns = get_prohibited_patterns()
        assert "test pattern 1" in patterns
        assert "test pattern 2" in patterns

    def test_get_harm_patterns(self):
        tmp = self._write_yaml(_SAMPLE_YAML)
        reload(str(tmp))
        patterns = get_harm_patterns()
        assert "harm pattern 1" in patterns

    def test_get_jailbreak_patterns(self):
        tmp = self._write_yaml(_SAMPLE_YAML)
        reload(str(tmp))
        patterns = get_jailbreak_patterns()
        assert "jailbreak pattern 1" in patterns

    def test_get_severe_output_patterns(self):
        tmp = self._write_yaml(_SAMPLE_YAML)
        reload(str(tmp))
        patterns = get_severe_output_patterns()
        assert "severe output 1" in patterns

    def test_get_medical_keywords(self):
        tmp = self._write_yaml(_SAMPLE_YAML)
        reload(str(tmp))
        keywords = get_medical_keywords()
        assert "test medical" in keywords

    def test_get_medical_disclaimer(self):
        tmp = self._write_yaml(_SAMPLE_YAML)
        reload(str(tmp))
        assert get_medical_disclaimer() == "Test disclaimer."

    def test_get_sub_agent_prompt_found(self):
        tmp = self._write_yaml(_SAMPLE_YAML)
        reload(str(tmp))
        assert get_sub_agent_prompt("legal") == "Legal sub-agent test"

    def test_get_sub_agent_prompt_not_found(self):
        tmp = self._write_yaml(_SAMPLE_YAML)
        reload(str(tmp))
        assert get_sub_agent_prompt("unknown") is None

    def test_get_episodic_memory_prompt(self):
        tmp = self._write_yaml(_SAMPLE_YAML)
        reload(str(tmp))
        result = get_episodic_memory_prompt("user: hello")
        assert "Extract from:" in result
        assert "user: hello" in result

    def test_max_history(self):
        tmp = self._write_yaml(_SAMPLE_YAML)
        reload(str(tmp))
        assert get_max_history() == 5

    def test_max_response_tokens(self):
        tmp = self._write_yaml(_SAMPLE_YAML)
        reload(str(tmp))
        assert get_max_response_tokens() == 400

    def test_missing_file_uses_empty_dict(self):
        fake = tempfile.NamedTemporaryFile(suffix='.nonexistent', delete=False)
        fake.close()
        fake_path = Path(fake.name)
        reload(str(fake_path))
        assert get_system_prompt() == ""

    def test_invalid_yaml_uses_empty_dict(self):
        tmp = self._write_yaml("{{{invalid yaml")
        reload(str(tmp))
        assert get_system_prompt() == ""

    def test_reload_twice_updates(self):
        tmp = self._write_yaml("system_prompt: \"First\"")
        reload(str(tmp))
        assert get_system_prompt() == "First"
        tmp.write_text("system_prompt: \"Second\"", encoding='utf-8')
        reload(str(tmp))
        assert get_system_prompt() == "Second"

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Versioned YAML-backed prompt and pattern loader.

All system prompts, prohibited patterns, safety patterns, and sub-agent
prompts are defined in ``system.yaml`` and loaded at startup.  In-memory
caching avoids repeated file I/O; a ``reload()`` function enables live
hot-reload for production use.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parent
_DEFAULT_YAML_PATH = _PROMPTS_DIR / "system.yaml"
_CACHE: dict[str, Any] = {}
_LOADED: bool = False


def _load(path: Path | None = None) -> dict[str, Any]:
    """Read and parse the YAML file, returning a flat dict with defaults."""
    global _CACHE, _LOADED
    if _LOADED:
        return _CACHE

    yaml_path = path or _DEFAULT_YAML_PATH
    if not yaml_path.is_file():
        logger.warning("Prompt file not found at %s — using empty defaults", yaml_path)
        _LOADED = True
        return _CACHE

    try:
        with open(yaml_path, encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
        _CACHE = raw if isinstance(raw, dict) else {}
        _LOADED = True
        logger.info("Loaded %d prompt keys from %s", len(_CACHE), yaml_path.name)
    except (OSError, yaml.YAMLError) as exc:
        logger.error("Failed to load prompt file %s: %s", yaml_path, exc)
        _LOADED = True

    return _CACHE


def reload(path: str | None = None) -> None:
    """Force re-read of the YAML file on the next access (hot-reload hook)."""
    global _CACHE, _LOADED
    _CACHE.clear()
    _LOADED = False
    _load(Path(path) if path else None)


# ── Specialised accessors (with safe defaults) ───────────────────────────────


def get_system_prompt() -> str:
    data = _load()
    return str(data.get("system_prompt", ""))


def get_prohibited_patterns() -> list[str]:
    data = _load()
    return list(data.get("prohibited_patterns", []))


def get_harm_patterns() -> tuple[str, ...]:
    data = _load()
    return tuple(data.get("harm_patterns", []))


def get_jailbreak_patterns() -> tuple[str, ...]:
    data = _load()
    return tuple(data.get("jailbreak_patterns", []))


def get_severe_output_patterns() -> tuple[str, ...]:
    data = _load()
    return tuple(data.get("severe_output_patterns", []))


def get_medical_keywords() -> tuple[str, ...]:
    data = _load()
    return tuple(data.get("medical_keywords", []))


def get_medical_disclaimer() -> str:
    data = _load()
    return str(data.get("medical_disclaimer", ""))


def get_sub_agent_prompt(intent: str) -> str | None:
    data = _load()
    agents = data.get("sub_agent_prompts", {})
    return agents.get(intent)


def get_episodic_memory_prompt(history_text: str) -> str:
    data = _load()
    template = data.get("episodic_memory_extraction_prompt", "")
    return template.replace("{history_text}", history_text)


def get_max_history() -> int:
    return int(_load().get("max_history", 10))


def get_max_response_tokens() -> int:
    return int(_load().get("max_response_tokens", 800))

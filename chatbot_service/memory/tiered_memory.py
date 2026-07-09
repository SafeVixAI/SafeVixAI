# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tiered memory system with three tiers for personalised, context-aware responses.

Tiers (fastest → most persistent):
  1. **Short-term (STM)** — in-memory dict keyed by ``user_id:session_id``.
     Holds recent utterances / facts discovered during the current conversation.
  2. **Session (context)** — conversation history already stored in Redis by
     ``ConversationMemoryStore`` (accessed via injected session history).
  3. **Long-term (LTM)** — pgvector-backed episodic memories extracted by
     ``EpisodicMemoryAgent`` from past sessions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from memory.user_memory import UserPreferenceStore

logger = logging.getLogger(__name__)


@dataclass
class TieredMemoryResult:
    """Unified result from all memory tiers."""
    user_preferences: dict[str, Any] = field(default_factory=dict)
    stm_facts: list[str] = field(default_factory=list)
    ltm_memories: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.user_preferences and not self.stm_facts and not self.ltm_memories

    def to_summary(self) -> str:
        """Build a human-readable summary of all tiers for LLM context injection."""
        parts: list[str] = []
        if self.user_preferences:
            lines = [f"{k}={v}" for k, v in self.user_preferences.items() if v]
            if lines:
                parts.append("User preferences: " + "; ".join(lines))
        if self.stm_facts:
            parts.append("Recent context: " + " | ".join(self.stm_facts))
        if self.ltm_memories:
            parts.append("Remembered facts: " + " | ".join(self.ltm_memories))
        return "\n".join(parts)


class TieredMemory:
    """Three-tier memory that combines user prefs, short-term facts, and long-term memories."""

    def __init__(
        self,
        pref_store: UserPreferenceStore | None = None,
        episodic_agent: Any = None,
    ) -> None:
        self.pref_store = pref_store
        self.episodic_agent = episodic_agent
        # Short-term memory: { "user_id:session_id": [fact, ...] }
        self._stm: dict[str, list[str]] = {}

    # ── Short-term memory operations ───────────────────────────────────────

    def _stm_key(self, user_id: str, session_id: str) -> str:
        return f"{user_id}:{session_id}"

    def add_stm_fact(self, user_id: str, session_id: str, fact: str) -> None:
        """Add a fact to short-term memory (in-memory, current session only)."""
        key = self._stm_key(user_id, session_id)
        if key not in self._stm:
            self._stm[key] = []
        self._stm[key].append(fact)
        # Keep only the 20 most recent facts per session
        if len(self._stm[key]) > 20:
            self._stm[key] = self._stm[key][-20:]

    def get_stm(self, user_id: str, session_id: str) -> list[str]:
        """Retrieve short-term memory facts for a session."""
        return list(self._stm.get(self._stm_key(user_id, session_id), []))

    def clear_stm(self, user_id: str, session_id: str) -> None:
        """Clear short-term memory for a session."""
        self._stm.pop(self._stm_key(user_id, session_id), None)

    def clear_all_stm(self) -> None:
        """Clear all short-term memory (e.g. on app shutdown)."""
        self._stm.clear()

    # ── Unified retrieval ──────────────────────────────────────────────────

    async def get_relevant(
        self,
        user_id: str | None,
        session_id: str,
        query: str,
    ) -> TieredMemoryResult:
        """Collect memories from all three tiers for the given user + session + query."""
        result = TieredMemoryResult()

        if not user_id or user_id in ('anonymous', 'authenticated', ''):
            return result

        # 1. User preferences (Redis)
        if self.pref_store:
            result.user_preferences = await self.pref_store.get_all_preferences(user_id)

        # 2. Short-term memory (in-memory)
        result.stm_facts = self.get_stm(user_id, session_id)

        # 3. Long-term memory (pgvector episodic)
        if self.episodic_agent:
            try:
                memories = await self.episodic_agent.retrieve_memory(user_id, query, top_k=3)
                result.ltm_memories = memories if memories else []
            except Exception as exc:
                logger.warning("LTM retrieval failed for %s: %s", user_id, exc)

        return result

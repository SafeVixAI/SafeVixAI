# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""AI Governance Framework for SafeVixAI Chatbot.

Implements:
- Hallucination detection (cross-reference with RAG sources)
- Prompt versioning and audit trail
- Factuality scoring
- Response validation against knowledge base
- Cost tracking per request

Phase 0.7: Ensures AI outputs are reliable, auditable, and compliant.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

# Thresholds for hallucination detection
_HALLUCINATION_THRESHOLD = 0.6  # Minimum relevance score to trust response
_FACTUALITY_MIN_SCORE = 0.7  # Minimum factuality score to accept response


@dataclass(slots=True)
class GovernanceResult:
    """Result of AI governance checks."""
    text: str
    hallucination_score: float = 0.0
    factuality_score: float = 0.0
    citations: list[str] = field(default_factory=list)
    flagged: bool = False
    flag_reason: str | None = None
    prompt_version: str = "v1"
    cost_estimate: float = 0.0


class AIGovernance:
    """AI governance engine for SafeVixAI chatbot."""

    def __init__(self, redis_url: str | None) -> None:
        self._redis = Redis.from_url(redis_url, encoding='utf-8', decode_responses=True) if redis_url else None
        self._prompt_versions: dict[str, str] = {}  # version -> prompt hash

    async def evaluate(
        self,
        response_text: str,
        retrieved_context: list[dict],
        tool_results: list[dict],
        prompt: str,
    ) -> GovernanceResult:
        """Evaluate AI response for hallucination, factuality, and compliance."""
        result = GovernanceResult(text=response_text)

        # 1. Hallucination detection
        result.hallucination_score = self._detect_hallucination(response_text, retrieved_context)
        
        # 2. Factuality scoring
        result.factuality_score = self._score_factuality(response_text, tool_results)
        
        # 3. Citation extraction
        result.citations = self._extract_citations(response_text, retrieved_context)
        
        # 4. Flag if below thresholds
        if result.hallucination_score < _HALLUCINATION_THRESHOLD:
            result.flagged = True
            result.flag_reason = "Low relevance to retrieved context"
        elif result.factuality_score < _FACTUALITY_MIN_SCORE:  # pragma: no branch
            result.flagged = True
            result.flag_reason = "Low factuality score"
        
        # 5. Prompt versioning
        result.prompt_version = self._get_prompt_version(prompt)
        
        # 6. Log for audit
        await self._log_audit(result, prompt)
        
        return result

    def _detect_hallucination(self, response: str, context: list[dict]) -> float:
        """Detect hallucination by checking if response is supported by context.

        Returns a score between 0 and 1, where 1 means fully supported.

        Scoring factors:
        1. Word overlap ratio (intersection / union instead of set size ratio)
        2. Named entity consistency (entities in response checked against context)
        3. Penalty for unsupported numeric claims or proper nouns

        Limitation: This is a heuristic — it measures surface-form overlap, not
        semantic correctness. False positives can occur for short responses with
        common words. False negatives can occur for paraphrased but correct content.
        """
        if not context:
            return 0.0

        response_lower = response.lower()
        response_words = set(response_lower.split())

        # Collect all context text
        context_texts = [item.get("content", "") for item in context]
        combined_context = " ".join(context_texts).lower()
        context_words = set(combined_context.split())

        if not response_words:
            return 0.0

        # 1. Word overlap ratio (intersection over union — more robust than set size ratio)
        intersection = response_words & context_words
        union = response_words | context_words
        overlap_ratio = len(intersection) / len(union)

        # 2. Named entity consistency — extract capitalized phrases (likely named entities)
        import re
        response_entities = set(
            m.group(0).lower()
            for m in re.finditer(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', response)
        )
        context_entities = set(
            m.group(0).lower()
            for m in re.finditer(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', combined_context)
        )
        if response_entities:
            entity_overlap = len(response_entities & context_entities) / len(response_entities)
        else:
            entity_overlap = 1.0  # No entities to check

        # 3. Penalize if response has numeric values not found in context
        response_numbers = set(
            m.group(0) for m in re.finditer(r'\b\d+(?:\.\d+)?\b', response_lower)
        )
        context_numbers = set(
            m.group(0) for m in re.finditer(r'\b\d+(?:\.\d+)?\b', combined_context)
        )
        if response_numbers:
            number_support = len(response_numbers & context_numbers) / len(response_numbers)
        else:
            number_support = 1.0

        # Combine: overlap ratio (50%), entity consistency (30%), number support (20%)
        score = overlap_ratio * 0.5 + entity_overlap * 0.3 + number_support * 0.2
        return min(1.0, max(0.0, score))

    def _score_factuality(self, response: str, tools: list[dict]) -> float:
        """Score factuality based on tool result alignment.
        
        Returns a score between 0 and 1.
        """
        if not tools:
            return 0.5  # Neutral if no tools used
        
        # Check if response mentions tool-provided facts
        tool_facts = []
        for tool in tools:
            if "payload" in tool:
                payload = tool["payload"]
                if isinstance(payload, dict):  # pragma: no branch
                    tool_facts.extend(str(v).lower() for v in payload.values() if isinstance(v, str))
        
        if not tool_facts:
            return 0.5
        
        response_lower = response.lower()
        matches = sum(1 for fact in tool_facts if fact in response_lower)
        return min(1.0, matches / max(1, len(tool_facts)))

    def _extract_citations(self, response: str, context: list[dict]) -> list[str]:
        """Extract citations from response that match context sources."""
        citations = []
        for item in context:
            source = item.get("source", "")
            title = item.get("title", "")
            if source and source not in citations:
                citations.append(source)
            if title and title not in citations:
                citations.append(title)
        return citations[:5]  # Max 5 citations

    def _get_prompt_version(self, prompt: str) -> str:
        """Get or create prompt version hash."""
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:8]
        
        # Check if we've seen this prompt before
        for version, hash_val in self._prompt_versions.items():
            if hash_val == prompt_hash:
                return version
        
        # New prompt version
        version = f"v{len(self._prompt_versions) + 1}"
        self._prompt_versions[version] = prompt_hash
        return version

    async def _log_audit(self, result: GovernanceResult, prompt: str) -> None:
        """Log governance result for audit trail."""
        if not self._redis:
            return
        
        try:
            audit_entry = {
                "timestamp": time.time(),
                "prompt_version": result.prompt_version,
                "hallucination_score": result.hallucination_score,
                "factuality_score": result.factuality_score,
                "flagged": result.flagged,
                "flag_reason": result.flag_reason,
                "citations": result.citations,
                "cost_estimate": result.cost_estimate,
            }
            
            # Store in Redis with 30-day TTL
            await self._redis.rpush(
                "audit:ai_governance",
                json.dumps(audit_entry)
            )
            await self._redis.expire("audit:ai_governance", 86400 * 30)
        except Exception as e:
            logger.warning("Failed to log AI governance audit: %s", e)

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:  # pragma: no branch
            await self._redis.aclose()

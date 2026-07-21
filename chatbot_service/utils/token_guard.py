# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

MAX_SAFE_INPUT_TOKENS = 4000
MAX_HISTORY_TOKENS = 6000

SYSTEM_PROMPT_FINGERPRINT = "You are SafeVixAI, an AI-powered road safety assistant"


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return len(text) // 4


def estimate_messages_tokens(messages: list[dict]) -> int:
    return sum(
        estimate_tokens(m.get("content", "") or "")
        for m in messages
    )


def trim_history(
    messages: list[dict], max_tokens: int = MAX_HISTORY_TOKENS
) -> list[dict]:
    total = estimate_messages_tokens(messages)
    if total <= max_tokens:
        return messages
    result = [messages[0]]
    for msg in reversed(messages[1:]):  # pragma: no branch
        result.insert(1, msg)
        if estimate_messages_tokens(result) > max_tokens:
            result.pop(1)
            break
    return result


def should_skip_groq(messages: list[dict]) -> bool:
    return estimate_messages_tokens(messages) > MAX_SAFE_INPUT_TOKENS


def sanitize_output(response: str) -> str:
    if len(response) < 20:
        return response
    if SYSTEM_PROMPT_FINGERPRINT[:30].lower() in response.lower():
        return (
            "I cannot reveal my system instructions. "
            "How can I help you with road safety?"
        )
    return response

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class AIIssueService:
    """AI-powered issue categorization, summarization, and suggested fixes.

    Uses keyword and pattern matching as a zero-dependency fallback when
    the LLM service is unavailable or for simple/obvious categorizations.
    """

    CATEGORY_KEYWORDS: dict[str, list[str]] = {
        'ui_bug': ['button', 'layout', 'css', 'style', 'overlap', 'broken ui', 'missing element'],
        'api_error': ['500', '502', '503', 'timeout', 'api', 'endpoint', 'response'],
        'data_loss': ['lost data', 'data missing', 'not saved', 'deleted', 'disappeared'],
        'auth': ['login', 'logout', 'token', 'session', 'unauthorized', 'forbidden', '403', '401'],
        'performance': ['slow', 'lag', 'hang', 'freeze', 'timeout', 'memory', 'cpu', 'loading'],
        'crash': ['crash', 'segfault', 'exception', 'fatal', 'panic', 'unexpected error'],
        'network': ['offline', 'connection', 'network', 'no internet', 'disconnected'],
        'security': ['xss', 'csrf', 'injection', 'vulnerability', 'exposure', 'leak'],
        'compatibility': ['firefox', 'safari', 'edge', 'mobile', 'android', 'ios', 'safari'],
    }

    SUGGESTED_FIXES: dict[str, str] = {
        'ui_bug': 'Clear your browser cache and reload. If the issue persists, try a different browser and include a screenshot.',
        'api_error': 'Check the network tab for the failing request URL. Verify the backend service is running and reachable.',
        'data_loss': 'Check the browser console for any errors. Try clearing IndexedDB and reloading the page.',
        'auth': 'Try logging out and logging back in. Clear your session cookies and local storage.',
        'performance': 'Close unused tabs and check Task Manager for memory usage. Try disabling browser extensions.',
        'crash': 'Update SafeVixAI to the latest version. Try clearing the app cache in Settings.',
        'network': 'Check your internet connection. The app requires a stable connection for some features.',
        'security': 'Do not share exploit details publicly. Contact the security team directly.',
        'compatibility': 'SafeVixAI works best on the latest Chrome or Edge. Consider updating your browser.',
    }

    async def categorize(self, *, title: str, description: str) -> dict[str, Any]:
        text = f'{title} {description}'.lower()

        best_category = 'other'
        best_score = 0

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > best_score:
                best_score = score
                best_category = category

        confidence = min(best_score / 3.0, 0.95) if best_score > 0 else 0.1

        return {'category': best_category, 'confidence': round(confidence, 2), 'matched_keywords': best_score}

    async def summarize(self, *, title: str, description: str, max_words: int = 50) -> str:
        sentences = description.replace('\n', ' ').split('.')
        meaningful = [s.strip() for s in sentences if len(s.strip()) > 20]

        if not meaningful:
            return title[:200]

        words = []
        for sentence in meaningful:
            for w in sentence.split():
                words.append(w)
                if len(words) >= max_words:
                    break
            if len(words) >= max_words:
                break

        summary = ' '.join(words)
        if len(meaningful) > 1 and len(words) >= max_words:
            summary += '...'
        return summary

    async def suggest_fix(self, *, title: str, description: str, category: str | None = None) -> str | None:
        if category and category in self.SUGGESTED_FIXES:
            return self.SUGGESTED_FIXES[category]

        text = f'{title} {description}'.lower()
        for cat, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return self.SUGGESTED_FIXES.get(cat)

        return None

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import json
import logging
import re

from config import Settings

logger = logging.getLogger(__name__)


FALLBACK_GUIDES = {
    'bleeding': {
        'title': 'Severe bleeding',
        'steps': [
            'Apply firm direct pressure using a clean cloth or bandage.',
            'Keep the injured area elevated if it does not worsen pain.',
            'Do not remove soaked cloth; add more layers over it.',
            'Call 112 or get emergency transport immediately for heavy bleeding.',
        ],
    },
    'burn': {
        'title': 'Burns',
        'steps': [
            'Cool the burn under cool running water for at least 20 minutes.',
            'Remove tight jewelry or clothing near the area if not stuck to the skin.',
            'Cover with a clean, non-fluffy dressing.',
            'Do not apply ice, toothpaste, or oily home remedies.',
        ],
    },
    'fracture': {
        'title': 'Suspected fracture',
        'steps': [
            'Keep the injured limb still and supported.',
            'Do not force the bone back into place.',
            'Apply a cold pack wrapped in cloth to reduce swelling.',
            'Seek urgent medical care, especially for severe pain or deformity.',
        ],
    },
    'cpr': {
        'title': 'CPR',
        'steps': [
            'Call 112 and ask for an ambulance immediately.',
            'Begin hard, fast chest compressions in the center of the chest.',
            'If trained, use cycles of 30 compressions and 2 rescue breaths.',
            'Continue until help arrives or the person starts breathing normally.',
        ],
    },
}


class FirstAidTool:
    def __init__(self, settings: Settings) -> None:
        self._data_path = settings.rag_data_dir / 'first_aid.json'
        self._guides = self._load_guides()

    def lookup(self, query: str) -> dict | None:
        text = query.lower()
        for key, guide in self._guides.items():
            keywords = [k for k in (guide.get('keywords') or [key, guide.get('title', ''), guide.get('category', '')]) if k]
            if any(keyword.lower() in text for keyword in keywords):
                return guide
        return None

    def _load_guides(self) -> dict[str, dict]:
        if not self._data_path.exists():
            return FALLBACK_GUIDES
        try:
            payload = json.loads(self._data_path.read_text(encoding='utf-8'))
        except (OSError, FileNotFoundError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load first aid guides: %s", exc)
            return FALLBACK_GUIDES
        if isinstance(payload, dict) and payload:
            return payload
        if isinstance(payload, list):
            normalized = self._normalize_article_list(payload)
            if normalized:
                return normalized
        return FALLBACK_GUIDES

    @staticmethod
    def _normalize_article_list(payload: list[dict]) -> dict[str, dict]:
        guides: dict[str, dict] = {}
        for article in payload:
            if not isinstance(article, dict):
                continue
            title = str(article.get('title') or '').strip()
            category = str(article.get('category') or '').strip().lower()
            article_id = str(article.get('id') or '').strip()
            steps = article.get('steps') or []
            if not title or not isinstance(steps, list) or not steps:
                continue
            key = article_id or category or re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')
            warning = article.get('warning')
            guide = {
                'id': article_id or key,
                'title': title,
                'category': category or None,
                'steps': [str(step).strip() for step in steps if str(step).strip()],
                'call_ambulance_if': [
                    str(condition).strip()
                    for condition in (article.get('call_ambulance_if') or [])
                    if str(condition).strip()
                ],
                'warning': str(warning).strip() if warning else None,
            }
            keywords = [guide['id'], title, category]
            guides[key] = {
                **guide,
                'keywords': [item for item in keywords if item],
            }
        return guides

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("safevixai.report_classifier")

ISSUE_CATEGORIES = {
    "pothole": {"keywords": ["pothole", "pot hole", "crater", "dip", "depression"], "default_severity": 3},
    "crack": {"keywords": ["crack", "fissure", "split", "fracture"], "default_severity": 2},
    "broken_signal": {"keywords": ["signal", "traffic light", "signal not working", "signal broken"], "default_severity": 4},
    "road_hazard": {"keywords": ["hazard", "debris", "obstacle", "blockage", "fallen tree", "spill"], "default_severity": 4},
    "damaged_road": {"keywords": ["damaged road", "bad road", "worn road", "rough road", "uneven"], "default_severity": 3},
    "flooding": {"keywords": ["flood", "water logging", "waterlogged", "drain", "blocked drain"], "default_severity": 4},
    "streetlight": {"keywords": ["street light", "streetlight", "light not working", "no light", "dark"], "default_severity": 2},
    "guardrail": {"keywords": ["guardrail", "railing", "barrier", "crash barrier", "metal rail"], "default_severity": 3},
    "signage": {"keywords": ["sign", "signboard", "road sign", "signage", "missing sign"], "default_severity": 2},
    "pedestrian": {"keywords": ["footpath", "sidewalk", "pedestrian", "crossing", "zebra"], "default_severity": 3},
    "encroachment": {"keywords": ["encroach", "illegal", "obstruction", "vendor", "parked"], "default_severity": 2},
}

SEVERITY_KEYWORDS: dict[int, list[str]] = {
    5: ["fatal", "death", "critical", "life threatening", "emergency", "severe injury", "collapse"],
    4: ["accident", "crash", "collision", "major", "dangerous", "urgent", "hazardous"],
    3: ["damage", "broken", "moderate", "disruptive", "injured"],
    2: ["minor", "small", "slight", "cosmetic", "superficial"],
    1: ["notice", "cosmetic", "surface", "trivial", "minimal"],
}


class ReportClassifier:
    def classify(self, description: str | None, issue_type: str | None = None) -> dict[str, Any]:
        if not description:
            return self._empty_result(issue_type)

        text = description.lower().strip()

        classified_type, confidence = self._classify_issue_type(text, issue_type)
        severity, severity_confidence = self._classify_severity(text)

        result = {
            "issue_type": classified_type,
            "issue_type_confidence": round(confidence, 2),
            "severity": severity,
            "severity_confidence": round(severity_confidence, 2),
            "classification_method": "rule_based",
            "matched_keywords": self._extract_matched_keywords(text),
        }

        logger.info(
            "Classified report: type=%s (%.2f), severity=%d (%.2f)",
            classified_type, confidence, severity, severity_confidence,
            extra={"service": "report_classifier"},
        )
        return result

    def _classify_issue_type(self, text: str, existing_type: str | None) -> tuple[str, float]:
        if existing_type and existing_type in ISSUE_CATEGORIES:
            return existing_type, 0.9

        best_match = "road_hazard"
        best_score = 0.0

        for category, config in ISSUE_CATEGORIES.items():
            for keyword in config["keywords"]:
                if keyword in text:
                    score = len(keyword) / max(len(text), 1) * 10
                    score = min(score, 1.0)
                    if score > best_score:
                        best_score = score
                        best_match = category

        confidence = max(best_score, 0.3)
        return best_match, confidence

    def _classify_severity(self, text: str) -> tuple[int, float]:
        for level in (5, 4, 3, 2, 1):
            for keyword in SEVERITY_KEYWORDS[level]:
                if keyword in text:
                    confidence = min(len(keyword) / max(len(text), 1) * 15, 1.0)
                    return level, max(confidence, 0.5)
        return 3, 0.3

    def _extract_matched_keywords(self, text: str) -> list[str]:
        matched = []
        for _category, config in ISSUE_CATEGORIES.items():
            for keyword in config["keywords"]:
                if keyword in text:
                    matched.append(keyword)
        if not matched:
            for level in (5, 4, 3, 2, 1):
                for kw in SEVERITY_KEYWORDS[level]:
                    if kw in text:
                        matched.append(kw)
        return matched[:5]

    @staticmethod
    def _empty_result(fallback_type: str | None) -> dict[str, Any]:
        return {
            "issue_type": fallback_type or "road_hazard",
            "issue_type_confidence": 0.5,
            "severity": 3,
            "severity_confidence": 0.3,
            "classification_method": "fallback",
            "matched_keywords": [],
        }

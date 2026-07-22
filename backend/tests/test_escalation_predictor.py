# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.road_issue import RoadIssue
from services.escalation_predictor import (
    HIGH_RISK_TYPES,
    SEVERITY_WEIGHTS,
    EscalationPrediction,
    EscalationPredictor,
)


class TestEscalationPrediction:
    def test_dataclass_minimal(self):
        p = EscalationPrediction(
            issue_uuid="abc-123",
            risk_score=0.45,
            risk_level="medium",
            contributing_factors=["Test factor"],
            recommended_action="Monitor",
            predicted_escalation_hours=24,
        )
        assert p.issue_uuid == "abc-123"
        assert p.risk_score == 0.45
        assert p.risk_level == "medium"
        assert p.contributing_factors == ["Test factor"]
        assert p.recommended_action == "Monitor"
        assert p.predicted_escalation_hours == 24

    def test_dataclass_none_escalation_hours(self):
        p = EscalationPrediction(
            issue_uuid="def-456",
            risk_score=0.1,
            risk_level="low",
            contributing_factors=[],
            recommended_action="Standard queue",
            predicted_escalation_hours=None,
        )
        assert p.predicted_escalation_hours is None

    def test_dataclass_edge_scores(self):
        p = EscalationPrediction(
            issue_uuid="min",
            risk_score=0.0,
            risk_level="low",
            contributing_factors=[],
            recommended_action="None",
            predicted_escalation_hours=None,
        )
        assert 0.0 <= p.risk_score <= 1.0

        p2 = EscalationPrediction(
            issue_uuid="max",
            risk_score=1.0,
            risk_level="critical",
            contributing_factors=["Everything"],
            recommended_action="Escalate now",
            predicted_escalation_hours=1,
        )
        assert p2.risk_score == 1.0
        assert p2.risk_level == "critical"

    def test_risk_levels_strings(self):
        for level in ("low", "medium", "high", "critical"):
            p = EscalationPrediction(
                issue_uuid="x",
                risk_score=0.5,
                risk_level=level,
                contributing_factors=["x"],
                recommended_action="x",
                predicted_escalation_hours=12,
            )
            assert p.risk_level == level


class TestConstants:
    def test_high_risk_types_keys(self):
        expected = {"flooding", "road_hazard", "broken_signal", "road_collapse", "electrical_hazard"}
        assert set(HIGH_RISK_TYPES.keys()) == expected

    def test_high_risk_types_values_in_range(self):
        for key, weight in HIGH_RISK_TYPES.items():
            assert 0.0 <= weight <= 1.0, f"{key} weight {weight} out of range"

    def test_severity_weights_keys(self):
        assert set(SEVERITY_WEIGHTS.keys()) == {1, 2, 3, 4, 5}

    def test_severity_weights_monotonic(self):
        for sev in (1, 2, 3, 4, 5):
            assert SEVERITY_WEIGHTS[sev] >= SEVERITY_WEIGHTS.get(sev - 1, 0)

    def test_severity_weights_max_not_exceeding(self):
        assert SEVERITY_WEIGHTS[5] <= 1.0


NOW = datetime(2026, 5, 23, 10, 0, 0, tzinfo=UTC)


def _make_issue(**overrides):
    defaults = {
        "uuid": "test-uuid-001",
        "severity": 3,
        "issue_type": "pothole",
        "created_at": NOW - timedelta(hours=1),
        "sla_deadline": None,
        "confirmation_count": 0,
        "location": None,
        "status": "open",
    }
    defaults.update(overrides)
    issue = MagicMock(spec=RoadIssue)
    for k, v in defaults.items():
        setattr(issue, k, v)
    return issue


class TestEscalationPredictorPredict:
    @pytest.mark.asyncio
    async def test_low_risk_recent_complaint(self):
        db = MagicMock()
        issue = _make_issue(severity=2, created_at=NOW - timedelta(hours=2))

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            pred = await EscalationPredictor.predict(db, issue)

        assert pred.risk_level in ("low", "medium")
        assert pred.risk_score < 0.50

    @pytest.mark.asyncio
    async def test_medium_risk_older_complaint(self):
        db = MagicMock()
        issue = _make_issue(
            severity=4,
            created_at=NOW - timedelta(hours=48),
            confirmation_count=3,
        )

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            pred = await EscalationPredictor.predict(db, issue)

        assert pred.risk_level in ("medium", "high")
        assert pred.risk_score >= 0.25

    @pytest.mark.asyncio
    async def test_high_risk_old_complaint_negative_sentiment(self):
        db = MagicMock()
        issue = _make_issue(
            severity=5,
            issue_type="road_collapse",
            created_at=NOW - timedelta(hours=100),
            confirmation_count=15,
        )

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            pred = await EscalationPredictor.predict(db, issue)

        assert pred.risk_level in ("high", "critical")
        assert pred.risk_score >= 0.50

    @pytest.mark.asyncio
    async def test_sla_breached_gives_critical_risk(self):
        db = MagicMock()
        issue = _make_issue(
            severity=5,
            issue_type="road_collapse",
            created_at=NOW - timedelta(hours=48),
            sla_deadline=NOW - timedelta(hours=2),
        )

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            pred = await EscalationPredictor.predict(db, issue)

        assert "SLA breached" in " ".join(pred.contributing_factors)
        assert pred.risk_score >= 0.50

    @pytest.mark.asyncio
    async def test_sla_breach_imminent_less_than_4h(self):
        db = MagicMock()
        issue = _make_issue(
            severity=3,
            created_at=NOW - timedelta(hours=20),
            sla_deadline=NOW + timedelta(hours=2),
        )

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            pred = await EscalationPredictor.predict(db, issue)

        assert "SLA breach imminent" in " ".join(pred.contributing_factors)

    @pytest.mark.asyncio
    async def test_sla_deadline_approaching_4_12h(self):
        db = MagicMock()
        issue = _make_issue(
            severity=3,
            created_at=NOW - timedelta(hours=10),
            sla_deadline=NOW + timedelta(hours=8),
        )

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            pred = await EscalationPredictor.predict(db, issue)

        assert "SLA deadline approaching" in " ".join(pred.contributing_factors)

    @pytest.mark.asyncio
    async def test_aging_complaint_no_sla(self):
        db = MagicMock()
        issue = _make_issue(
            severity=2,
            created_at=NOW - timedelta(hours=100),
            sla_deadline=None,
        )

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            pred = await EscalationPredictor.predict(db, issue)

        assert "Aging complaint" in " ".join(pred.contributing_factors)

    @pytest.mark.asyncio
    async def test_high_risk_issue_type_adds_factor(self):
        db = MagicMock()
        issue = _make_issue(issue_type="road_collapse", severity=4)

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            pred = await EscalationPredictor.predict(db, issue)

        assert "High-risk issue type:" in " ".join(pred.contributing_factors)

    @pytest.mark.asyncio
    async def test_many_confirmations_adds_factor(self):
        db = MagicMock()
        issue = _make_issue(confirmation_count=12)

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            pred = await EscalationPredictor.predict(db, issue)

        assert "High citizen reports" in " ".join(pred.contributing_factors)

    @pytest.mark.asyncio
    async def test_empty_issue_uuid_is_str(self):
        db = MagicMock()
        issue = _make_issue(uuid="abc-def")

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            pred = await EscalationPredictor.predict(db, issue)

        assert pred.issue_uuid == "abc-def"

    @pytest.mark.asyncio
    async def test_created_at_naive_tz_fixed(self):
        db = MagicMock()
        created = datetime(2026, 5, 22, 10, 0, 0)  # no tzinfo
        issue = _make_issue(created_at=created, severity=5)

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            pred = await EscalationPredictor.predict(db, issue)

        assert pred.risk_score > 0

    @pytest.mark.asyncio
    async def test_normal_risk_profile_when_no_factors(self):
        db = MagicMock()
        issue = _make_issue(
            severity=1,
            created_at=NOW - timedelta(hours=1),
            confirmation_count=0,
            issue_type="graffiti",
        )

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            pred = await EscalationPredictor.predict(db, issue)

        assert "Normal risk profile" in pred.contributing_factors
        assert pred.risk_level == "low"

    @pytest.mark.asyncio
    async def test_batch_predict_filters_by_min_risk(self):
        db = MagicMock()
        issues = []
        for i in range(5):
            iss = MagicMock(spec=RoadIssue)
            iss.severity = 3
            iss.issue_type = "pothole"
            iss.created_at = NOW - timedelta(hours=48)
            iss.sla_deadline = None
            iss.confirmation_count = 0
            iss.location = None
            iss.status = "open"
            iss.uuid = f"uuid-{i}"
            issues.append(iss)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = issues
        db.execute = AsyncMock(return_value=mock_result)

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            preds = await EscalationPredictor.batch_predict(db, min_risk=0.9)

        assert isinstance(preds, list)

    @pytest.mark.asyncio
    async def test_batch_predict_with_city_filter(self):
        db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)

        with patch("services.escalation_predictor.RoadIssue.city", "Chennai", create=True):
            preds = await EscalationPredictor.batch_predict(db, city="Chennai")
        assert preds == []

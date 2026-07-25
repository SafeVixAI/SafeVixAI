# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""AI Escalation Prediction service.

Rule-based + heuristic prediction for complaint escalation risk scoring.
Uses complaint metadata (age, severity, type, location density, citizen upvotes)
to predict whether a complaint will need escalation to a higher authority.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.road_issue import RoadIssue

logger = logging.getLogger(__name__)

# High-risk issue types that tend to escalate
HIGH_RISK_TYPES = {
    'flooding': 0.35,
    'road_hazard': 0.30,
    'broken_signal': 0.25,
    'road_collapse': 0.40,
    'electrical_hazard': 0.35,
}

# Severity risk multipliers
SEVERITY_WEIGHTS = {
    1: 0.05,
    2: 0.10,
    3: 0.20,
    4: 0.40,
    5: 0.60,
}


@dataclass
class EscalationPrediction:
    """Escalation risk prediction for a complaint."""
    issue_uuid: str
    risk_score: float          # 0.0 - 1.0
    risk_level: str            # low / medium / high / critical
    contributing_factors: list[str]
    recommended_action: str
    predicted_escalation_hours: int | None


class EscalationPredictor:
    """
    Heuristic-based escalation risk predictor.

    Scoring factors:
    1. Issue severity (40% weight)
    2. Time since filing / SLA proximity (25% weight)
    3. Issue type risk profile (15% weight)
    4. Citizen upvote/confirmation count (10% weight)
    5. Neighborhood complaint density (10% weight)
    """

    @staticmethod
    async def predict(
        db: AsyncSession,
        issue: RoadIssue,
    ) -> EscalationPrediction:
        """Predict escalation risk for a single complaint."""
        factors: list[str] = []
        score = 0.0

        # Factor 1: Severity (40%)
        sev = issue.severity or 3
        sev_score = SEVERITY_WEIGHTS.get(sev, 0.20)
        score += sev_score * 0.40
        if sev >= 4:
            factors.append(f"High severity ({sev}/5)")

        # Factor 2: SLA proximity / age (25%)
        now = datetime.now(UTC)
        age_hours = 0
        if issue.created_at:
            created = issue.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            age_hours = (now - created).total_seconds() / 3600

        sla_score = 0.0
        if issue.sla_deadline:
            deadline = issue.sla_deadline
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=UTC)
            hours_left = (deadline - now).total_seconds() / 3600
            if hours_left < 0:
                sla_score = 1.0
                factors.append(f"SLA breached ({abs(int(hours_left))}h overdue)")
            elif hours_left < 4:
                sla_score = 0.8
                factors.append(f"SLA breach imminent ({int(hours_left)}h left)")
            elif hours_left < 12:
                sla_score = 0.5
                factors.append(f"SLA deadline approaching ({int(hours_left)}h)")
            else:
                sla_score = 0.1
        elif age_hours > 72:
            sla_score = 0.7
            factors.append(f"Aging complaint ({int(age_hours)}h old, no SLA)")
        elif age_hours > 24:
            sla_score = 0.3

        score += sla_score * 0.25

        # Factor 3: Issue type risk (15%)
        type_risk = HIGH_RISK_TYPES.get(issue.issue_type or '', 0.10)
        score += type_risk * 0.15
        if type_risk >= 0.30:
            factors.append(f"High-risk issue type: {issue.issue_type}")

        # Factor 4: Citizen confirmations (10%)
        confirmations = getattr(issue, 'confirmation_count', 0) or 0
        if confirmations >= 10:
            conf_score = 1.0
            factors.append(f"High citizen reports ({confirmations} confirmations)")
        elif confirmations >= 5:
            conf_score = 0.6
            factors.append(f"Multiple citizen reports ({confirmations})")
        elif confirmations >= 2:
            conf_score = 0.3
        else:
            conf_score = 0.0
        score += conf_score * 0.10

        # Factor 5: Neighborhood density (10%)
        density_score = 0.0
        if issue.location:
            try:
                from geoalchemy2 import Geography
                from sqlalchemy import cast

                nearby_stmt = (
                    select(func.count(RoadIssue.id))
                    .where(RoadIssue.status.in_(["open", "acknowledged", "in_progress"]))
                    .where(RoadIssue.location.isnot(None))
                    .where(
                        func.ST_DWithin(
                            cast(RoadIssue.location, Geography),
                            cast(issue.location, Geography),
                            500  # 500m radius
                        )
                    )
                )
                nearby_count = (await db.execute(nearby_stmt)).scalar() or 0
                if nearby_count >= 10:
                    density_score = 1.0
                    factors.append(f"Hotspot area ({nearby_count} complaints within 500m)")
                elif nearby_count >= 5:
                    density_score = 0.5
                elif nearby_count >= 2:
                    density_score = 0.2
            except Exception as exc:
                logger.debug("Skip density check: %s", exc)
        score += density_score * 0.10

        # Clamp
        score = min(max(score, 0.0), 1.0)

        # Risk level
        if score >= 0.75:
            level = 'critical'
            action = 'Immediate escalation to zone officer and authority head. Prioritize for resolution within 4 hours.'
            predicted_hours = max(1, int(4 - age_hours)) if age_hours < 4 else 1
        elif score >= 0.50:
            level = 'high'
            action = 'Flag for supervisor review. Assign dedicated field officer within 12 hours.'
            predicted_hours = max(4, int(12 - age_hours)) if age_hours < 12 else 4
        elif score >= 0.25:
            level = 'medium'
            action = 'Monitor SLA timeline. Queue for next available field officer.'
            predicted_hours = max(12, int(48 - age_hours)) if age_hours < 48 else 12
        else:
            level = 'low'
            action = 'Standard processing queue. No immediate escalation needed.'
            predicted_hours = None

        if not factors:
            factors.append("Normal risk profile")

        return EscalationPrediction(
            issue_uuid=str(issue.uuid),
            risk_score=round(score, 3),
            risk_level=level,
            contributing_factors=factors,
            recommended_action=action,
            predicted_escalation_hours=predicted_hours,
        )

    @staticmethod
    async def batch_predict(
        db: AsyncSession,
        *,
        city: str | None = None,
        status_filter: list[str] | None = None,
        min_risk: float = 0.25,
    ) -> list[EscalationPrediction]:
        """Batch predict escalation risk for all open complaints."""
        if status_filter is None:
            status_filter = ["open", "acknowledged", "in_progress"]

        stmt = (
            select(RoadIssue)
            .where(RoadIssue.status.in_(status_filter))
        )
        if city:
            stmt = stmt.where(RoadIssue.city == city)

        result = await db.execute(stmt)
        issues = result.scalars().all()

        predictions = []
        for issue in issues:
            pred = await EscalationPredictor.predict(db, issue)
            if pred.risk_score >= min_risk:
                predictions.append(pred)

        predictions.sort(key=lambda p: p.risk_score, reverse=True)
        return predictions

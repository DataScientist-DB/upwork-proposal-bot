from __future__ import annotations

from app.config import DECISION_THRESHOLDS
from app.models import DecisionType, GateResult, ScoreBreakdown


def get_confidence_label(confidence: int) -> str:
    if confidence >= 75:
        return "HIGH"
    if confidence >= 50:
        return "MEDIUM"
    return "LOW"


def decide(gate: GateResult, scores: ScoreBreakdown) -> DecisionType:



    if not gate.passed:
        return "SKIP"

    if scores.final_score >= DECISION_THRESHOLDS["strong_apply"]:
        return "STRONG_APPLY"

    if scores.final_score >= DECISION_THRESHOLDS["apply"]:
        return "APPLY"

    if scores.final_score >= DECISION_THRESHOLDS["conditional"]:

        high_risk = (
                scores.competition_risk >= 65
                or scores.client_quality < 45
                or scores.execution_risk >= 65
                or (
                        scores.clarity < 40
                        and scores.client_quality < 60
                )
        )

        medium_risk = (
                scores.competition_risk >= 55
                or scores.client_quality < 50
                or (
                        scores.clarity < 40
                        and scores.execution_risk >= 50
                )
        )

        if high_risk:
            return "CONDITIONAL_APPLY"

        if medium_risk and scores.final_score < DECISION_THRESHOLDS["apply"] - 5:
            return "CONDITIONAL_APPLY"

        return "APPLY"


    return "SKIP"
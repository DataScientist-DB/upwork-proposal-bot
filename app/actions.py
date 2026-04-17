from __future__ import annotations

from app.config import MIN_AUTO_APPLY_CONFIDENCE, MIN_AUTO_APPLY_SCORE, MIN_PREMIUM_SCORE
from app.models import ActionPlan, DecisionType, JobInput, ScoreBreakdown


def choose_proposal_mode(decision: DecisionType, scores: ScoreBreakdown) -> str:
    if decision == "STRONG_APPLY":
        return "PREMIUM"

    if decision == "APPLY" and scores.final_score >= MIN_PREMIUM_SCORE and scores.technical_fit >= 75:
        return "PREMIUM"

    if decision in {"APPLY", "CONDITIONAL_APPLY"}:
        return "STANDARD"

    return "NONE"


def should_boost(decision: DecisionType, job: JobInput, scores: ScoreBreakdown) -> bool:
    return (
        decision == "STRONG_APPLY"
        and (job.proposals_count is not None and job.proposals_count <= 15)
        and scores.client_quality >= 60
        and scores.value >= 65
        and scores.final_score >= 80
    )


def should_auto_apply(decision: DecisionType, scores: ScoreBreakdown) -> bool:
    return (
        decision == "STRONG_APPLY"
        and scores.final_score >= MIN_AUTO_APPLY_SCORE
        and scores.confidence >= MIN_AUTO_APPLY_CONFIDENCE
        and scores.technical_fit >= 80
        and scores.client_quality >= 60
    )


def estimate_bid_range(job: JobInput, scores: ScoreBreakdown) -> tuple[float | None, float | None, float | None, str]:
    if job.budget_min:
        low = float(job.budget_min)
        mid = float(max(job.budget_min, (job.budget_max or job.budget_min * 1.5)))
        high = float(max(mid, low * 2.0))
    elif job.hourly_min or job.hourly_max:
        low = float(job.hourly_min or 25)
        mid = float(job.hourly_max or max(low, 50))
        high = float(max(mid, low * 1.6))
    else:
        low, mid, high = 300.0, 800.0, 1800.0

    if scores.value >= 70:
        mode = "MID_TO_HIGH"
    elif scores.final_score >= 60:
        mode = "LOW_TO_MID"
    else:
        mode = "LOW_ONLY"

    return low, mid, high, mode


def build_action_plan(decision: DecisionType, job: JobInput, scores: ScoreBreakdown) -> ActionPlan:
    if decision == "SKIP":
        return ActionPlan()

    bid_low, bid_mid, bid_high, pricing_mode = estimate_bid_range(job, scores)

    return ActionPlan(
        proposal_mode=choose_proposal_mode(decision, scores),
        should_boost=should_boost(decision, job, scores),
        auto_apply=should_auto_apply(decision, scores),
        pricing_mode=pricing_mode,
        bid_low=bid_low,
        bid_mid=bid_mid,
        bid_high=bid_high,
    )
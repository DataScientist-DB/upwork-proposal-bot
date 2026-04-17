from __future__ import annotations

from app.models import (
    ActionPlan,
    EvaluationResult,
    GateResult,
    JobInput,
    ParsedSignals,
    ScoreBreakdown,
)
from app.parser import parse_job
from app.gates import run_gate
from app.decision import decide, get_confidence_label
from app.strategy import build_strategy
from app.explain import build_reasons, build_risks
from app.scoring import (
    adjust_probability,
    calculate_score,
    calculate_win_probability,
    detect_complexity,
    score_client_quality,
    score_competition_risk,
    score_skill,
    score_timing,
    score_value,
)


# ========================
# MAIN ENGINE
# ========================

def evaluate_job(job: JobInput) -> EvaluationResult:
    """
    Full evaluation pipeline:
    1. Parse signals
    2. Gate filtering
    3. Scoring
    4. Decision
    5. Strategy
    6. Explanation
    """

    # ------------------------
    # 1. PARSE
    # ------------------------
    parsed: ParsedSignals = parse_job(job)

    # ------------------------
    # 2. GATE
    # ------------------------
    gate: GateResult = run_gate(job, parsed)

    # ------------------------
    # 3. SCORING
    # ------------------------
    normalized_proposals = _normalize_proposals(job.proposals_count)
    normalized_last_viewed = _normalize_last_viewed(job.last_viewed_hours_ago)
    normalized_budget = _extract_budget(job)

    skill_score = score_skill(job.description)
    competition_risk = score_competition_risk(normalized_proposals)

    client_score = score_client_quality(
        client_hire_rate=job.client_hire_rate,
        client_total_spent=job.client_total_spent,
        payment_verified=job.payment_verified,
        client_reviews_count=job.client_reviews_count,
        client_avg_hourly_rate=job.client_avg_hourly_rate,
        last_viewed_hours_ago=job.last_viewed_hours_ago,
    )

    complexity = detect_complexity(job.description)

    timing_score = score_timing(
        proposals=normalized_proposals,
        interviewing=int(job.interviewing_count or 0),
        invites_sent=int(job.invites_sent or 0),
        last_viewed_hours_ago=job.last_viewed_hours_ago,
    )

    value_score = score_value(
        budget=normalized_budget,
        complexity=complexity,
        timing=timing_score,
        competition_risk=competition_risk,
        client_quality=client_score,
        clarity_score=parsed.clarity_score,
    )

    final_score = calculate_score(
        text=job.description,
        proposals=normalized_proposals,
        last_viewed=normalized_last_viewed,
        interviewing=int(job.interviewing_count or 0),
        invites_sent=int(job.invites_sent or 0),
        unanswered_invites=int(job.unanswered_invites or 0),
        budget=normalized_budget,
        hires=int(job.client_hire_rate or 0),
        total_spent=int(job.client_total_spent or 0),
        payment_verified=job.payment_verified,
        client_hire_rate=job.client_hire_rate,
        client_reviews_count=job.client_reviews_count,
        client_avg_hourly_rate=job.client_avg_hourly_rate,
        last_viewed_hours_ago=job.last_viewed_hours_ago,
        clarity_score=parsed.clarity_score,
    )

    scores = ScoreBreakdown(
        technical_fit=skill_score,
        client_quality=client_score,
        competition_risk=competition_risk,
        value=value_score,
        timing=timing_score,
        clarity=parsed.clarity_score,
        execution_risk=parsed.execution_risk_score,
        confidence=_compute_confidence(job, parsed),
        final_score=final_score,
    )

    # ------------------------
    # 4. DECISION
    # ------------------------
    decision = decide(gate, scores)

    # ------------------------
    # 5. PROBABILITY
    # ------------------------
    base_prob = calculate_win_probability(scores.final_score)
    win_probability = adjust_probability(base_prob, scores)

    # ------------------------
    # 6. STRATEGY (ACTION)
    # ------------------------
    strategy_dict = build_strategy(
        text=job.description,
        score=scores.final_score,
        skill_score=scores.technical_fit,
        proposals=normalized_proposals,
        client_quality=scores.client_quality,
        value_score=scores.value,
        decision=decision,
        budget=normalized_budget,
        win_probability=win_probability,
        clarity=scores.clarity,
        timing=scores.timing,
        competition_risk=scores.competition_risk,
    )

    action = ActionPlan(
        proposal_mode=_map_proposal_mode(strategy_dict["proposal_mode"]),
        should_boost=strategy_dict["should_boost"],
        auto_apply=strategy_dict["auto_apply"],
        pricing_mode=strategy_dict.get("pricing_mode", "NONE"),
        bid_low=strategy_dict["bid_low"],
        bid_mid=strategy_dict["bid_avg"],
        bid_high=strategy_dict["bid_high"],
    )

    # ------------------------
    # 7. CONFIDENCE
    # ------------------------
    confidence_label = get_confidence_label(scores.confidence)

    # ------------------------
    # 8. EXPLANATION
    # ------------------------
    result = EvaluationResult(
        gate=gate,
        scores=scores,
        decision=decision,
        confidence_label=confidence_label,
        reasons=[],
        risks=[],
        action=action,
    )

    result.win_probability = win_probability
    result.reasons = build_reasons(job, parsed, result)
    result.risks = build_risks(job, parsed, result)

    return result


# ========================
# HELPERS
# ========================

def _normalize_proposals(proposals_count: int | None) -> str:
    """
    Convert numeric proposals to scoring categories aligned with UI buckets.
    """
    if proposals_count is None:
        return "unknown"

    if proposals_count < 5:
        return "Less than 5"
    if proposals_count <= 10:
        return "5 to 10"
    if proposals_count <= 20:
        return "10 to 20"
    if proposals_count <= 50:
        return "20 to 50"
    return "50+"


def _extract_budget(job: JobInput) -> int | None:
    """
    Normalize budget for scoring and strategy layer.
    """
    if job.budget_max:
        return int(job.budget_max)

    if job.budget_min:
        return int(job.budget_min)

    if job.hourly_max:
        return int(job.hourly_max * 40)  # rough monthly proxy

    if job.hourly_min:
        return int(job.hourly_min * 40)

    return None


def _map_proposal_mode(mode: str) -> str:
    """
    Convert strategy output -> model enum
    """
    mapping = {
        "premium": "PREMIUM",
        "standard": "STANDARD",
        "shortlist_only": "STANDARD",
        "none": "NONE",
    }
    return mapping.get((mode or "").lower(), "NONE")


def _normalize_last_viewed(hours):
    if hours is None:
        return "unknown"
    if hours <= 1:
        return "just now"
    if hours <= 24:
        return "today"
    if hours <= 48:
        return "yesterday"
    return "older"


def _compute_confidence(job: JobInput, parsed: ParsedSignals) -> int:
    """
    Simple confidence score:
    - higher when client/job data is more complete
    - lower when important fields are missing or the parsed clarity is weak
    """
    score = 50

    if job.title:
        score += 5
    if job.description and len(job.description.strip()) >= 80:
        score += 10
    elif job.description:
        score += 4

    if job.client_hire_rate is not None:
        score += 8
    if job.client_total_spent is not None:
        score += 6
    if job.client_reviews_count is not None:
        score += 5
    if job.last_viewed_hours_ago is not None:
        score += 6
    if job.proposals_count is not None:
        score += 5

    if parsed.clarity_score < 30:
        score -= 12
    elif parsed.clarity_score < 50:
        score -= 6

    if parsed.execution_risk_score >= 70:
        score -= 8
    elif parsed.execution_risk_score >= 50:
        score -= 4

    return max(0, min(100, int(score)))
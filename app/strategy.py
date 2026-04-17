from __future__ import annotations

from typing import Any, Dict


def build_strategy(
    text: str,
    score: int,
    skill_score: int,
    proposals: str,
    client_quality: int,
    value_score: int,
    decision: str,
    budget: int | None = None,
    win_probability: int | None = None,
    clarity: int | None = None,
    timing: int | None = None,
    competition_risk: int | None = None,
) -> Dict[str, Any]:
    """
    Strategy layer:
    decides how to act on a job after scoring/decision.

    Outputs:
    - proposal_mode: premium | standard | none
    - should_boost: bool
    - auto_apply: bool
    - pricing_mode: aggressive | balanced | conservative | none
    - bid_low / bid_avg / bid_high
    """

    normalized_decision = (decision or "").upper()

    # ------------------------------------------------------------
    # 1) Hard stop for skip
    # ------------------------------------------------------------
    if normalized_decision == "SKIP":
        bid_anchor = _resolve_bid_anchor(budget)
        return {
            "proposal_mode": "none",
            "should_boost": False,
            "auto_apply": False,
            "pricing_mode": "none",
            "bid_low": bid_anchor,
            "bid_avg": bid_anchor,
            "bid_high": bid_anchor,
        }

    # ------------------------------------------------------------
    # 2) Proposal mode
    # ------------------------------------------------------------
    proposal_mode = _choose_proposal_mode(
        decision=normalized_decision,
        score=score,
        skill_score=skill_score,
        client_quality=client_quality,
        value_score=value_score,
        win_probability=win_probability,
        clarity=clarity,
    )

    # ------------------------------------------------------------
    # 3) Boost decision
    # ------------------------------------------------------------
    should_boost = _should_boost(
        decision=normalized_decision,
        win_probability=win_probability,
        value_score=value_score,
        client_quality=client_quality,
        clarity=clarity,
        competition_risk=competition_risk,
        timing=timing,
        budget=budget,
    )

    # ------------------------------------------------------------
    # 4) Auto apply decision
    # ------------------------------------------------------------
    auto_apply = _should_auto_apply(
        decision=normalized_decision,
        proposal_mode=proposal_mode,
        score=score,
        skill_score=skill_score,
        client_quality=client_quality,
        value_score=value_score,
        clarity=clarity,
        timing=timing,
        competition_risk=competition_risk,
        should_boost=should_boost,
    )

    # ------------------------------------------------------------
    # 5) Pricing mode
    # ------------------------------------------------------------
    pricing_mode = _choose_pricing_mode(
        decision=normalized_decision,
        client_quality=client_quality,
        value_score=value_score,
        clarity=clarity,
        timing=timing,
        competition_risk=competition_risk,
        budget=budget,
    )

    # ------------------------------------------------------------
    # 6) Bid range
    # ------------------------------------------------------------
    bid_low, bid_avg, bid_high = _build_bid_range(
        budget=budget,
        pricing_mode=pricing_mode,
        proposal_mode=proposal_mode,
        value_score=value_score,
        client_quality=client_quality,
        clarity=clarity,
    )

    return {
        "proposal_mode": proposal_mode,
        "should_boost": should_boost,
        "auto_apply": auto_apply,
        "pricing_mode": pricing_mode,
        "bid_low": bid_low,
        "bid_avg": bid_avg,
        "bid_high": bid_high,
    }


# ============================================================
# PROPOSAL MODE
# ============================================================

def _choose_proposal_mode(
    decision: str,
    score: int,
    skill_score: int,
    client_quality: int,
    value_score: int,
    win_probability: int | None,
    clarity: int | None,
) -> str:
    if decision == "SKIP":
        return "none"

    wp = win_probability if win_probability is not None else 0
    cl = clarity if clarity is not None else 50

    premium_conditions = [
        decision == "STRONG_APPLY",
        score >= 75,
        skill_score >= 70,
        client_quality >= 60,
        value_score >= 60,
        wp >= 65,
        cl >= 45,
    ]

    if sum(1 for x in premium_conditions if x) >= 5:
        return "premium"

    if decision in {"APPLY", "CONDITIONAL_APPLY", "STRONG_APPLY"}:
        return "standard"

    return "none"


# ============================================================
# BOOST
# ============================================================

def _should_boost(
    decision: str,
    win_probability: int | None,
    value_score: int,
    client_quality: int,
    clarity: int | None,
    competition_risk: int | None,
    timing: int | None,
    budget: int | None,
) -> bool:
    """
    Boost = spend extra connects for visibility.
    Should be strict and relatively rare.
    """

    if decision not in {"APPLY", "STRONG_APPLY"}:
        return False

    wp = win_probability if win_probability is not None else 0
    cl = clarity if clarity is not None else 50
    cr = competition_risk if competition_risk is not None else 50
    tm = timing if timing is not None else 50

    if wp < 68:
        return False

    if value_score < 60:
        return False

    if client_quality < 55:
        return False

    if cl < 45:
        return False

    if cr >= 70:
        return False

    if tm < 50:
        return False

    if budget is not None and budget < 150:
        return False

    return True


# ============================================================
# AUTO APPLY
# ============================================================

def _should_auto_apply(
    decision: str,
    proposal_mode: str,
    score: int,
    skill_score: int,
    client_quality: int,
    value_score: int,
    clarity: int | None,
    timing: int | None,
    competition_risk: int | None,
    should_boost: bool,
) -> bool:
    """
    Auto-apply should be very conservative.
    Only for clean, solid, standard opportunities.
    """

    if decision != "STRONG_APPLY":
        return False

    if proposal_mode != "standard":
        return False

    if should_boost:
        return False

    cl = clarity if clarity is not None else 50
    tm = timing if timing is not None else 50
    cr = competition_risk if competition_risk is not None else 50

    if score < 78:
        return False

    if skill_score < 72:
        return False

    if client_quality < 60:
        return False

    if value_score < 58:
        return False

    if cl < 55:
        return False

    if tm < 60:
        return False

    if cr >= 60:
        return False

    return True


# ============================================================
# PRICING MODE
# ============================================================

def _choose_pricing_mode(
    decision: str,
    client_quality: int,
    value_score: int,
    clarity: int | None,
    timing: int | None,
    competition_risk: int | None,
    budget: int | None,
) -> str:
    if decision == "SKIP":
        return "none"

    cl = clarity if clarity is not None else 50
    tm = timing if timing is not None else 50
    cr = competition_risk if competition_risk is not None else 50

    if budget is None:
        return "balanced"

    # Strong opportunity -> price with confidence
    if (
        value_score >= 70
        and client_quality >= 65
        and cl >= 55
        and tm >= 55
        and cr < 60
    ):
        return "aggressive"

    # Weak / unclear -> stay careful
    if value_score < 50 or cl < 40 or client_quality < 50:
        return "conservative"

    return "balanced"


# ============================================================
# BID RANGE
# ============================================================

def _build_bid_range(
    budget: int | None,
    pricing_mode: str,
    proposal_mode: str,
    value_score: int,
    client_quality: int,
    clarity: int | None,
) -> tuple[int | None, int | None, int | None]:
    if budget is None or budget <= 0:
        return None, None, None

    cl = clarity if clarity is not None else 50
    anchor = _resolve_bid_anchor(budget)

    if pricing_mode == "none":
        return anchor, anchor, anchor

    if pricing_mode == "conservative":
        low = round(anchor * 0.85)
        mid = round(anchor * 0.95)
        high = anchor
        return _normalize_bid_triplet(low, mid, high, budget)

    if pricing_mode == "aggressive":
        low = round(anchor * 0.95)
        mid = anchor
        high = round(anchor * 1.10)
        return _normalize_bid_triplet(low, mid, high, budget)

    # balanced
    # adjust slightly based on quality
    premium_bias = 0
    if proposal_mode == "premium":
        premium_bias += 3
    if value_score >= 65:
        premium_bias += 2
    if client_quality >= 65:
        premium_bias += 2
    if cl < 40:
        premium_bias -= 4

    low = round(anchor * 0.90)
    mid = anchor + premium_bias
    high = round(anchor * 1.05) + premium_bias

    return _normalize_bid_triplet(low, mid, high, budget)


def _resolve_bid_anchor(budget: int | None) -> int | None:
    if budget is None or budget <= 0:
        return None
    return int(round(budget))


def _normalize_bid_triplet(
    low: int | None,
    mid: int | None,
    high: int | None,
    budget: int | None,
) -> tuple[int | None, int | None, int | None]:
    if budget is None or budget <= 0:
        return None, None, None

    safe_low = max(1, min(int(low), int(budget)))
    safe_mid = max(safe_low, min(int(mid), int(budget)))
    safe_high = max(safe_mid, min(int(high), int(budget)))

    return safe_low, safe_mid, safe_high
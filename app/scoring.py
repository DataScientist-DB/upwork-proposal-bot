from __future__ import annotations

import math
from typing import Dict, List, Optional


# ========================
# CLASSIFIER SIGNALS
# ========================

STRONG_KEYWORDS: Dict[str, List[str]] = {
    "scraping": ["scrape", "scraping", "extract", "crawler", "data extraction"],
    "automation": ["automation", "bot", "workflow", "selenium", "playwright"],
    "apify": ["apify", "actor", "crawlee"],
    "data_pipeline": ["etl", "pipeline", "csv", "xlsx", "json", "data processing"],
    "python_backend": ["python", "fastapi", "api", "backend"],
    "ai_llm": ["openai", "gpt", "llm", "rag"],
}

CATEGORY_WEIGHTS = {
    "scraping": 6,
    "automation": 5,
    "apify": 7,
    "data_pipeline": 5,
    "python_backend": 5,
    "ai_llm": 4,
}

WEAK_SIGNALS = ["logo design", "wordpress", "figma only"]
EXCLUSION_SIGNALS = ["commission only", "cold calling"]


# ========================
# HELPERS
# ========================

def normalize_text(text: str) -> str:
    return " ".join((text or "").lower().strip().split())


def clamp(value: float, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, int(round(value))))


def _find_matches(text: str, keywords: List[str]) -> List[str]:
    found = []
    for kw in keywords:
        if kw in text:
            found.append(kw)
    return list(set(found))


def _to_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


# ========================
# CLASSIFICATION
# ========================

def extract_signals(text: str):
    text = normalize_text(text)

    matched_categories = []
    matched_keywords = {}

    for category, keywords in STRONG_KEYWORDS.items():
        found = _find_matches(text, keywords)
        if found:
            matched_categories.append(category)
            matched_keywords[category] = found

    weak = _find_matches(text, WEAK_SIGNALS)
    exclusion = _find_matches(text, EXCLUSION_SIGNALS)

    return matched_categories, matched_keywords, weak, exclusion


# ========================
# SCORING COMPONENTS
# ========================

def score_skill(text: str) -> int:
    categories, keywords, weak, exclusion = extract_signals(text)

    score = 0

    for cat in categories:
        base = CATEGORY_WEIGHTS.get(cat, 0)
        bonus = min(len(keywords[cat]), 3)
        score += base + bonus

    if weak:
        score -= 5 * len(weak)

    if exclusion:
        score -= 10 * len(exclusion)

    return max(0, min(100, score * 4))


def score_competition_risk(proposals: str) -> int:
    """
    Competition risk = how crowded the opportunity is.
    Higher score means harder to win.
    """
    if proposals == "Less than 5":
        return 20
    if proposals == "5 to 10":
        return 30
    if proposals == "10 to 20":
        return 45
    if proposals == "20 to 50":
        return 75
    if proposals == "50+":
        return 90
    return 50


def score_client_quality(
    client_hire_rate: float | int | None = None,
    client_total_spent: float | int | None = None,
    payment_verified: bool = False,
    client_reviews_count: int | None = None,
    client_avg_hourly_rate: float | int | None = None,
    last_viewed_hours_ago: float | int | None = None,
    hires: int | None = None,          # backward compatibility
    total_spent: int | None = None,    # backward compatibility
) -> int:
    """
    Client quality = seriousness + reliability + engagement.

    Main drivers:
    - hire rate (dominant)
    - payment verification
    - spend history
    - reviews
    - average hourly rate
    - recent client engagement (last viewed)
    """

    if client_total_spent is None and total_spent is not None:
        client_total_spent = total_spent

    if client_hire_rate is None and hires is not None:
        if hires <= 0:
            client_hire_rate = 0
        elif hires == 1:
            client_hire_rate = 20
        elif hires == 2:
            client_hire_rate = 35
        elif hires <= 4:
            client_hire_rate = 50
        else:
            client_hire_rate = 65

    score = 50.0

    # 1) Hire rate = dominant
    hire_rate = _to_float(client_hire_rate, 0.0)

    if hire_rate < 10:
        score -= 30
    elif hire_rate < 20:
        score -= 22
    elif hire_rate < 30:
        score -= 15
    elif hire_rate < 40:
        score -= 8
    elif hire_rate < 60:
        score += 0
    elif hire_rate < 75:
        score += 8
    else:
        score += 15

    # 2) Payment verification
    if payment_verified:
        score += 8
    else:
        score -= 8

    # 3) Spend history
    spent = _to_float(client_total_spent, 0.0)

    if spent <= 0:
        score -= 8
    elif spent < 500:
        score -= 3
    elif spent < 2000:
        score += 2
    elif spent < 10000:
        score += 6
    elif spent < 50000:
        score += 10
    else:
        score += 14

    # 4) Reviews
    reviews = 0 if client_reviews_count is None else int(client_reviews_count)

    if reviews <= 0:
        score -= 5
    elif reviews < 5:
        score += 1
    elif reviews < 20:
        score += 4
    elif reviews < 50:
        score += 7
    else:
        score += 9

    # 5) Avg hourly rate
    avg_rate = _to_float(client_avg_hourly_rate, 0.0)

    if avg_rate <= 0:
        score += 0
    elif avg_rate < 10:
        score -= 4
    elif avg_rate < 20:
        score -= 2
    elif avg_rate < 40:
        score += 2
    elif avg_rate < 80:
        score += 4
    else:
        score += 5

    # 6) Recent engagement
    hours = _to_float(last_viewed_hours_ago, -1)

    if hours < 0:
        score += 0
    elif hours <= 1:
        score += 8
    elif hours <= 6:
        score += 6
    elif hours <= 24:
        score += 3
    elif hours <= 72:
        score -= 2
    else:
        score -= 6

    # 7) Hard caps by hire rate
    if hire_rate < 10:
        score = min(score, 35)
    elif hire_rate < 20:
        score = min(score, 45)
    elif hire_rate < 25:
        score = min(score, 50)
    elif hire_rate < 30:
        score = min(score, 58)

    return clamp(score)


def detect_complexity(text: str) -> str:
    text = normalize_text(text)

    if any(x in text for x in ["saas", "architecture", "scalable", "rag", "trading bot"]):
        return "high"

    if any(x in text for x in ["api", "dashboard", "automation", "pipeline"]):
        return "medium"

    return "low"


def score_timing(
    proposals: str,
    interviewing: int = 0,
    invites_sent: int = 0,
    last_viewed_hours_ago: float | int | None = None,
) -> int:
    """
    Timing = how early you are in the hiring process.
    Uses proposal volume, interview progress, invite activity,
    and recent client attention.
    """
    if proposals == "Less than 5":
        score = 95
    elif proposals == "5 to 10":
        score = 85
    elif proposals == "10 to 20":
        score = 65
    elif proposals == "20 to 50":
        score = 40
    elif proposals == "50+":
        score = 20
    else:
        score = 50

    # Interviewing = process already moving
    if interviewing >= 1:
        score -= 8
    if interviewing >= 3:
        score -= 10
    if interviewing >= 5:
        score -= 10

    # Invites = active sourcing, often later / more competitive stage
    if invites_sent >= 3:
        score -= 4
    if invites_sent >= 8:
        score -= 6
    if invites_sent >= 15:
        score -= 8

    # Recent view is only a light timing signal
    if last_viewed_hours_ago is not None:
        hours = _to_float(last_viewed_hours_ago, -1)
        if hours >= 0:
            if hours <= 1:
                score += 3
            elif hours <= 24:
                score += 1
            elif hours > 72:
                score -= 3

    return max(0, min(100, int(round(score))))


def score_value(
    budget: int | None,
    complexity: str,
    timing: int | None = None,
    competition_risk: int | None = None,
    client_quality: int | None = None,
    clarity_score: int | None = None,
) -> int:
    """
    Value = is this opportunity worth your effort overall?

    It combines:
    - economics (budget vs complexity)
    - timing
    - competition risk
    - client quality
    - clarity
    """

    # 1) Base economic value
    if not budget:
        base = 50
    elif complexity == "high":
        base = 80 if budget >= 3000 else 40
    elif complexity == "medium":
        base = 75 if budget >= 1000 else 45
    else:
        base = 65 if budget >= 300 else 50

    # 2) Timing adjustment
    if timing is not None:
        if timing >= 85:
            base += 8
        elif timing >= 65:
            base += 4
        elif timing < 40:
            base -= 8
        elif timing < 55:
            base -= 4

    # 3) Competition adjustment
    if competition_risk is not None:
        if competition_risk >= 75:
            base -= 10
        elif competition_risk >= 60:
            base -= 6
        elif competition_risk <= 30:
            base += 4

    # 4) Client quality adjustment
    if client_quality is not None:
        if client_quality >= 75:
            base += 8
        elif client_quality >= 60:
            base += 4
        elif client_quality < 45:
            base -= 10
        elif client_quality < 55:
            base -= 5

    # 5) Clarity adjustment
    if clarity_score is not None:
        if clarity_score < 30:
            base -= 10
        elif clarity_score < 50:
            base -= 5
        elif clarity_score >= 75:
            base += 3

    return max(0, min(100, int(round(base))))


# ========================
# FINAL SCORE
# ========================

def calculate_score(
    text: str,
    proposals: str,
    last_viewed: str,
    interviewing: int,
    invites_sent: int,
    unanswered_invites: int,
    budget: Optional[int],
    hires: int,
    total_spent: int,
    payment_verified: bool,
    client_hire_rate: float | int | None = None,
    client_reviews_count: int | None = None,
    client_avg_hourly_rate: float | int | None = None,
    last_viewed_hours_ago: float | int | None = None,
    clarity_score: int | None = None,
):
    skill = score_skill(text)
    comp_risk = score_competition_risk(proposals)

    client = score_client_quality(
        client_hire_rate=client_hire_rate,
        client_total_spent=total_spent,
        payment_verified=payment_verified,
        client_reviews_count=client_reviews_count,
        client_avg_hourly_rate=client_avg_hourly_rate,
        last_viewed_hours_ago=last_viewed_hours_ago,
        hires=hires,
        total_spent=total_spent,
    )

    complexity = detect_complexity(text)

    timing = score_timing(
        proposals=proposals,
        interviewing=interviewing,
        invites_sent=invites_sent,
        last_viewed_hours_ago=last_viewed_hours_ago,
    )

    value = score_value(
        budget=budget,
        complexity=complexity,
        timing=timing,
        competition_risk=comp_risk,
        client_quality=client,
        clarity_score=clarity_score,
    )

    score = int(
        skill * 0.30 +
        (100 - comp_risk) * 0.20 +
        client * 0.15 +
        value * 0.20 +
        timing * 0.15
    )

    # Market signal adjustments
    if interviewing >= 3:
        score -= 5

    if invites_sent >= 10:
        score -= 4

    if unanswered_invites >= 5:
        score += 4

    if invites_sent >= 5 and unanswered_invites >= 5:
        score += 3

    return max(0, min(100, score))


def calculate_win_probability(score: int) -> int:
    """
    Convert score (0-100) into a realistic win probability.
    """
    prob = 1 / (1 + math.exp(-(score - 55) / 12))
    return int(prob * 100)


def adjust_probability(prob: int, scores) -> int:
    """
    Apply conservative adjustments based on key signals.
    """
    if scores.competition_risk <= 30:
        prob += 4
    elif scores.competition_risk >= 70:
        prob -= 8

    if scores.client_quality >= 70:
        prob += 4
    elif scores.client_quality < 45:
        prob -= 6

    if scores.clarity < 45:
        prob -= 4

    if scores.execution_risk >= 60:
        prob -= 5

    return max(5, min(90, prob))
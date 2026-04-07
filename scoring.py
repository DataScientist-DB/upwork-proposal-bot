from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import re


STRONG_KEYWORDS: Dict[str, List[str]] = {
    "scraping": [
        "scrape",
        "scraping",
        "extract",
        "extraction",
        "crawler",
        "crawl",
        "parsing",
        "parser",
        "data extraction",
        "web scraping",
        "website scraping",
        "data mining",
        "lead generation",
        "directory scraping",
    ],
    "automation": [
        "automation",
        "bot",
        "workflow",
        "automate",
        "script",
        "browser automation",
        "process automation",
        "task automation",
        "selenium",
        "playwright",
    ],
    "apify": [
        "apify",
        "actor",
        "actors",
        "apify actor",
        "apify store",
        "crawlee",
    ],
    "dashboard": [
        "streamlit",
        "dashboard",
        "analytics dashboard",
        "internal tool",
        "admin panel",
        "reporting dashboard",
        "data dashboard",
        "monitoring dashboard",
    ],
    "data_pipeline": [
        "etl",
        "pipeline",
        "data pipeline",
        "csv",
        "xlsx",
        "json",
        "cleaning",
        "transform",
        "data processing",
        "data validation",
        "data enrichment",
        "normalization",
        "export",
    ],
    "documents": [
        "pdf",
        "report",
        "document generation",
        "invoice",
        "export",
        "reporting",
        "summary report",
        "executive summary",
        "xlsx export",
        "csv export",
    ],
    "python_backend": [
        "python",
        "fastapi",
        "flask",
        "api",
        "rest api",
        "backend",
        "integration",
    ],
    "ai_llm": [
        "openai",
        "gpt",
        "llm",
        "rag",
        "ai assistant",
        "prompt",
        "proposal generator",
        "ai workflow",
    ],
    "trading_prediction": [
        "polymarket",
        "prediction market",
        "prediction markets",
        "market analyzer",
        "trading bot",
        "scalper",
        "market signals",
        "arbitrage",
        "liquidity",
        "clob",
        "gamma api",
        "kalshi",
        "crypto trading",
        "execution engine",
        "trading automation",
        "market data",
        "signal detection",
        "alpha signals",
        "momentum",
        "risk management",
        "order book",
        "market intelligence",
    ],
}

CATEGORY_WEIGHTS: Dict[str, int] = {
    "scraping": 6,
    "automation": 5,
    "apify": 7,
    "dashboard": 5,
    "data_pipeline": 5,
    "documents": 3,
    "python_backend": 5,
    "ai_llm": 4,
    "trading_prediction": 6,
}

WEAK_SIGNALS: List[str] = [
    "logo design",
    "figma only",
    "react native",
    "ios app",
    "android app",
    "unity engine",
    "game development",
    "3d modeling",
    "illustration",
    "branding",
    "wordpress theme",
    "shopify theme design",
    "video editing",
    "animation",
]

EXCLUSION_SIGNALS: List[str] = [
    "commission-only",
    "commission only",
    "cold calling",
    "appointment setting",
    "sales representative",
    "crypto shill",
]

WEAK_SIGNAL_PENALTY = 6
EXCLUSION_SIGNAL_PENALTY = 12

PREMIUM_THRESHOLD = 24
STANDARD_THRESHOLD = 16


@dataclass
class ScoreResult:
    score: int
    recommendation: str
    matched_categories: List[str]
    matched_keywords: Dict[str, List[str]]
    weak_signals_found: List[str]
    exclusion_signals_found: List[str]
    reasons: List[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class WinProbabilityResult:
    base_score: int
    activity_score: int
    final_score: int
    probability_label: str
    apply_strategy: str
    bid_low: int
    bid_avg: int
    bid_high: int
    recommended_bid: int
    complexity: str
    reasons: List[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class WinProbabilityV2:
    skill_score: int
    competition_score: int
    client_score: int
    value_score: int
    timing_score: int
    final_score: int
    decision: str
    recommended_bid: int
    bid_low: int
    bid_avg: int
    bid_high: int
    complexity: str
    proposal_mode: str
    auto_apply: bool
    reasons: List[str]

    def to_dict(self) -> dict:
        return asdict(self)


def normalize_text(text: str) -> str:
    return " ".join((text or "").lower().strip().split())


def _find_matches(text: str, keywords: List[str]) -> List[str]:
    text = text.lower()
    found: List[str] = []

    for keyword in keywords:
        keyword = keyword.lower()

        if len(keyword) <= 6:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, text):
                found.append(keyword)
        else:
            if keyword in text:
                found.append(keyword)

    return sorted(set(found))


def _safe_int(value, default: int = 0) -> int:
    try:
        if value is None:
            return default
        if isinstance(value, int):
            return value
        text = str(value).strip().replace(",", "")
        match = re.search(r"\d+", text)
        return int(match.group()) if match else default
    except Exception:
        return default


def extract_match_reasons(text: str) -> dict:
    normalized = normalize_text(text)

    matched_keywords: Dict[str, List[str]] = {}
    matched_categories: List[str] = []

    for category, keywords in STRONG_KEYWORDS.items():
        found = _find_matches(normalized, keywords)
        if found:
            matched_keywords[category] = found
            matched_categories.append(category)

    weak_found = _find_matches(normalized, WEAK_SIGNALS)
    exclusion_found = _find_matches(normalized, EXCLUSION_SIGNALS)

    return {
        "matched_keywords": matched_keywords,
        "matched_categories": matched_categories,
        "weak_signals_found": weak_found,
        "exclusion_signals_found": exclusion_found,
    }


def classify_job_fit(score: int) -> str:
    if score >= PREMIUM_THRESHOLD:
        return "premium"
    if score >= STANDARD_THRESHOLD:
        return "standard"
    return "skip"


def score_job(text: str) -> ScoreResult:
    analysis = extract_match_reasons(text)

    matched_keywords: Dict[str, List[str]] = analysis["matched_keywords"]
    matched_categories: List[str] = analysis["matched_categories"]
    weak_signals_found: List[str] = analysis["weak_signals_found"]
    exclusion_signals_found: List[str] = analysis["exclusion_signals_found"]

    score = 0
    reasons: List[str] = []

    label_map = {
        "scraping": "scraping/data extraction",
        "automation": "automation/bot development",
        "apify": "Apify/Crawlee ecosystem",
        "dashboard": "dashboard/internal tools",
        "data_pipeline": "data pipelines/exports",
        "documents": "reporting/doc generation",
        "python_backend": "Python/backend/API",
        "ai_llm": "AI/LLM workflows",
        "trading_prediction": "prediction markets/trading automation",
    }

    for category in matched_categories:
        base_weight = CATEGORY_WEIGHTS.get(category, 0)
        keyword_bonus = min(len(matched_keywords[category]), 3)
        category_score = base_weight + keyword_bonus
        score += category_score

        pretty_label = label_map.get(category, category)
        reasons.append(
            f"Strong match in {pretty_label}: +{category_score} ({', '.join(matched_keywords[category])})"
        )

    if weak_signals_found:
        penalty = WEAK_SIGNAL_PENALTY * len(weak_signals_found)
        score -= penalty
        reasons.append(
            f"Weak-fit signals: -{penalty} ({', '.join(weak_signals_found)})"
        )

    if exclusion_signals_found:
        penalty = EXCLUSION_SIGNAL_PENALTY * len(exclusion_signals_found)
        score -= penalty
        reasons.append(
            f"Exclusion signals: -{penalty} ({', '.join(exclusion_signals_found)})"
        )

    if "scraping" in matched_categories and not exclusion_signals_found and score < 15:
        score = 15
        reasons.append("Applied scraping floor → upgraded to minimum viable score (15)")

    if "automation" in matched_categories and not exclusion_signals_found and score < 15:
        score = 15
        reasons.append("Applied automation floor → upgraded to minimum viable score (15)")

    score = max(score, 0)
    recommendation = classify_job_fit(score)

    reasons.append(f"Final recommendation: {recommendation.upper()}")

    return ScoreResult(
        score=score,
        recommendation=recommendation,
        matched_categories=matched_categories,
        matched_keywords=matched_keywords,
        weak_signals_found=weak_signals_found,
        exclusion_signals_found=exclusion_signals_found,
        reasons=reasons,
    )


def adjust_score_with_activity(
    score: int,
    proposals: str,
    last_viewed: str,
    interviewing: int,
    invites_sent: int,
    unanswered_invites: int,
):
    reasons: List[str] = []

    if proposals == "50+":
        score -= 8
        reasons.append("Very high competition (50+ proposals): -8")
    elif proposals == "20 to 50":
        score -= 5
        reasons.append("High competition (20 to 50 proposals): -5")
    elif proposals == "15 to 20":
        score -= 3
        reasons.append("Moderate competition (15 to 20 proposals): -3")
    elif proposals == "10 to 15":
        score -= 1
        reasons.append("Some competition (10 to 15 proposals): -1")
    elif proposals == "Less than 5":
        score += 6
        reasons.append("Low competition (Less than 5 proposals): +6")
    elif proposals == "5 to 10":
        score += 3
        reasons.append("Manageable competition (5 to 10 proposals): +3")

    if last_viewed == "just now":
        score += 5
        reasons.append("Client viewed job just now: +5")
    elif last_viewed == "today":
        score += 4
        reasons.append("Client viewed job today: +4")
    elif last_viewed == "yesterday":
        score += 1
        reasons.append("Client viewed job yesterday: +1")
    elif last_viewed == "2 to 3 days ago":
        score -= 2
        reasons.append("Client has not viewed in 2 to 3 days: -2")
    elif last_viewed == "4 to 7 days ago":
        score -= 4
        reasons.append("Client has not viewed in 4 to 7 days: -4")
    elif last_viewed == "more than 1 week ago":
        score -= 6
        reasons.append("Client inactive for more than 1 week: -6")

    # Interviewing = late-stage competition
    if interviewing >= 5:
        score -= 5
        reasons.append("Client is already interviewing many candidates: -5")
    elif interviewing >= 3:
        score -= 3
        reasons.append("Client is interviewing multiple candidates: -3")
    elif interviewing >= 1:
        score -= 1
        reasons.append("Client has started interviewing: -1")
    else:
        reasons.append("No one currently interviewing: +0")

    # Invites sent = mild competition / noisy outreach
    if invites_sent >= 10:
        score -= 3
        reasons.append("Client mass-inviting many freelancers: -3")
    elif invites_sent >= 5:
        score -= 2
        reasons.append("Client sending multiple invites: -2")
    elif invites_sent >= 1:
        score -= 1
        reasons.append("Client sent some invites: -1")
    else:
        reasons.append("No invites sent: +0")

    # Unanswered invites = opportunity signal
    if unanswered_invites >= 10:
        score += 5
        reasons.append("Very high unanswered invites → strong opportunity: +5")
    elif unanswered_invites >= 5:
        score += 3
        reasons.append("High unanswered invites → good opportunity: +3")
    elif unanswered_invites >= 1:
        score += 1
        reasons.append("Some unanswered invites → slight opportunity: +1")
    else:
        reasons.append("All invites answered → no gap: +0")

    # Opportunity spike: high invites + high unanswered
    if invites_sent >= 10 and unanswered_invites >= 7:
        score += 4
        reasons.append("Opportunity spike detected: client invited many but got weak response: +4")
    elif invites_sent >= 5 and unanswered_invites >= 5:
        score += 2
        reasons.append("Opportunity spike detected: outreach is underperforming: +2")

    return score, reasons


def detect_complexity(text: str) -> str:
    text = normalize_text(text)

    high_terms = [
        "saas",
        "platform",
        "architecture",
        "multi-tenant",
        "scalable",
        "ai agent",
        "bot",
        "job matching system",
        "automation engine",
        "production system",
        "llm",
        "rag",
        "trading bot",
        "prediction market",
        "execution engine",
        "market analyzer",
        "order book",
        "arbitrage",
        "risk management",
        "signal detection",
    ]
    medium_terms = [
        "apify",
        "crawlee",
        "playwright",
        "fastapi",
        "api",
        "dashboard",
        "database",
        "pipeline",
        "multiple websites",
        "lead generation",
        "streamlit",
        "integration",
        "polymarket",
        "kalshi",
        "market data",
        "crypto trading",
        "automation",
    ]

    if any(term in text for term in high_terms):
        return "high"
    if any(term in text for term in medium_terms):
        return "medium"
    return "low"


def estimate_bid_range(text: str, client_budget: Optional[int] = None) -> Dict[str, int]:
    complexity = detect_complexity(text)

    ranges = {
        "low": {"low": 100, "avg": 300, "high": 600},
        "medium": {"low": 400, "avg": 1000, "high": 2500},
        "high": {"low": 1500, "avg": 3500, "high": 7000},
    }

    bid_range = ranges[complexity].copy()

    if client_budget and client_budget > 0:
        if client_budget < bid_range["low"]:
            bid_range["low"] = client_budget
            bid_range["avg"] = client_budget
            bid_range["high"] = client_budget
        elif bid_range["low"] <= client_budget <= bid_range["high"]:
            bid_range["avg"] = client_budget

    return bid_range


def classify_probability(score: int) -> tuple[str, str]:
    if score >= 80:
        return "very strong", "apply aggressively"
    if score >= 65:
        return "strong", "apply"
    if score >= 50:
        return "moderate", "selective apply"
    return "weak", "skip"


def recommend_bid(win_score: int, bid_range: Dict[str, int], fit_recommendation: str) -> int:
    if fit_recommendation == "skip" or win_score < 50:
        return 0
    if win_score >= 80:
        return bid_range["avg"]
    if win_score >= 65:
        return int((bid_range["avg"] + bid_range["high"]) / 2)
    return bid_range["high"]


def calculate_win_probability(
    text: str,
    proposals: str,
    last_viewed: str,
    interviewing: int,
    invites_sent: int,
    unanswered_invites: int,
    client_budget: Optional[int] = None,
) -> WinProbabilityResult:
    base = score_job(text)
    activity_score, activity_reasons = adjust_score_with_activity(
        score=base.score,
        proposals=proposals,
        last_viewed=last_viewed,
        interviewing=_safe_int(interviewing),
        invites_sent=_safe_int(invites_sent),
        unanswered_invites=_safe_int(unanswered_invites),
    )

    base_score = base.score
    final_score = max(0, min(100, 35 + activity_score))

    complexity = detect_complexity(text)
    bid_range = estimate_bid_range(text, client_budget=client_budget)
    probability_label, apply_strategy = classify_probability(final_score)
    recommended_bid = recommend_bid(final_score, bid_range, base.recommendation)

    reasons: List[str] = []
    reasons.extend(base.reasons)
    reasons.extend(activity_reasons)
    reasons.append(f"Complexity detected: {complexity}")
    reasons.append(
        f"Bid range estimate → low: ${bid_range['low']}, avg: ${bid_range['avg']}, high: ${bid_range['high']}"
    )
    reasons.append(f"Win probability: {final_score}/100 ({probability_label})")
    reasons.append(f"Recommended action: {apply_strategy}")
    if recommended_bid > 0:
        reasons.append(f"Recommended bid: ${recommended_bid}")
    else:
        reasons.append("Recommended bid: skip")

    return WinProbabilityResult(
        base_score=base_score,
        activity_score=activity_score,
        final_score=final_score,
        probability_label=probability_label,
        apply_strategy=apply_strategy,
        bid_low=bid_range["low"],
        bid_avg=bid_range["avg"],
        bid_high=bid_range["high"],
        recommended_bid=recommended_bid,
        complexity=complexity,
        reasons=reasons,
    )


def score_competition(proposals: str) -> tuple[int, str]:
    if proposals == "Less than 5":
        return 90, "Very low competition"
    if proposals == "5 to 10":
        return 75, "Low competition"
    if proposals == "10 to 15":
        return 60, "Moderate competition"
    if proposals == "15 to 20":
        return 45, "High competition"
    if proposals == "20 to 50":
        return 30, "Very high competition"
    if proposals == "50+":
        return 15, "Extreme competition"
    return 50, "Unknown competition"


def score_client(
    hires: int = 0,
    total_spent: int = 0,
    payment_verified: bool = False,
) -> tuple[int, str]:
    score = 50
    reasons: List[str] = []

    if hires == 0:
        score -= 15
        reasons.append("No hire history")
    else:
        score += 10
        reasons.append("Client has hiring history")

    if total_spent >= 10000:
        score += 20
        reasons.append("High spender")
    elif total_spent >= 1000:
        score += 10
        reasons.append("Moderate spender")
    elif total_spent > 0:
        score += 4
        reasons.append("Some spend history")

    if payment_verified:
        score += 10
        reasons.append("Payment verified")
    else:
        reasons.append("Payment not verified/unknown")

    return max(0, min(100, score)), ", ".join(reasons)


def score_value(client_budget: Optional[int], complexity: str) -> tuple[int, str]:
    if not client_budget:
        return 50, "No budget info"

    if complexity == "high":
        if client_budget >= 3000:
            return 90, "Strong ROI"
        elif client_budget >= 1500:
            return 70, "Acceptable ROI"
        return 30, "Underpriced for complexity"

    if complexity == "medium":
        if client_budget >= 1000:
            return 85, "Good ROI"
        elif client_budget >= 500:
            return 65, "Acceptable ROI"
        return 35, "Low budget"

    if client_budget >= 300:
        return 70, "Reasonable for simple job"
    return 55, "Simple job but low budget"


def score_timing(last_viewed: str) -> tuple[int, str]:
    if last_viewed == "just now":
        return 95, "Client active now"
    if last_viewed == "today":
        return 85, "Client active today"
    if last_viewed == "yesterday":
        return 70, "Recently active"
    if "days ago" in (last_viewed or ""):
        return 40, "Cooling down"
    if last_viewed == "more than 1 week ago":
        return 20, "Cold client"
    return 50, "Unknown timing"


def classify_decision(score: int) -> str:
    if score >= 75:
        return "APPLY (AGGRESSIVE)"
    if score >= 60:
        return "APPLY"
    if score >= 45:
        return "SELECTIVE"
    return "SKIP"


def choose_proposal_mode(final_score: int, fit_recommendation: str) -> str:
    if fit_recommendation == "premium" and final_score >= 75:
        return "premium"
    if final_score >= 60:
        return "standard"
    if final_score >= 45:
        return "shortlist_only"
    return "skip"


def should_auto_apply(
    final_score: int,
    fit_recommendation: str,
    client_budget: Optional[int],
    proposals: str,
) -> bool:
    if fit_recommendation == "skip":
        return False
    if final_score < 78:
        return False
    if proposals in {"20 to 50", "50+"}:
        return False
    if client_budget is not None and client_budget > 0 and client_budget < 300:
        return False
    return True


def calculate_win_probability_v2(
    text: str,
    proposals: str,
    last_viewed: str,
    interviewing: int,
    invites_sent: int,
    unanswered_invites: int,
    client_budget: Optional[int] = None,
    hires: int = 0,
    total_spent: int = 0,
    payment_verified: bool = False,
) -> WinProbabilityV2:
    base = score_job(text)
    complexity = detect_complexity(text)
    bid_range = estimate_bid_range(text, client_budget)

    skill_score = min(100, base.score * 4)
    competition_score, comp_reason = score_competition(proposals)
    client_score, client_reason = score_client(
        hires=hires,
        total_spent=total_spent,
        payment_verified=payment_verified,
    )
    value_score, value_reason = score_value(client_budget, complexity)
    timing_score, timing_reason = score_timing(last_viewed)

    final_score = int(
        skill_score * 0.30
        + competition_score * 0.20
        + client_score * 0.15
        + value_score * 0.20
        + timing_score * 0.15
    )

    # Interviewing = late-stage competition
    if interviewing >= 5:
        final_score -= 6
    elif interviewing >= 3:
        final_score -= 4
    elif interviewing >= 1:
        final_score -= 2

    # Invites sent = mild competition/noise
    if invites_sent >= 10:
        final_score -= 4
    elif invites_sent >= 5:
        final_score -= 2
    elif invites_sent >= 1:
        final_score -= 1

    # Unanswered invites = opportunity signal
    if unanswered_invites >= 10:
        final_score += 6
    elif unanswered_invites >= 5:
        final_score += 4
    elif unanswered_invites >= 1:
        final_score += 2

    # Opportunity spike detector
    if invites_sent >= 10 and unanswered_invites >= 7:
        final_score += 6
    elif invites_sent >= 5 and unanswered_invites >= 5:
        final_score += 3

    final_score = max(0, min(100, final_score))

    decision = classify_decision(final_score)
    recommended_bid = recommend_bid(final_score, bid_range, base.recommendation)
    proposal_mode = choose_proposal_mode(final_score, base.recommendation)
    auto_apply = should_auto_apply(
        final_score=final_score,
        fit_recommendation=base.recommendation,
        client_budget=client_budget,
        proposals=proposals,
    )

    reasons = [
        f"Fit recommendation: {base.recommendation.upper()}",
        f"Skill match: {skill_score}/100",
        f"Competition: {competition_score}/100 ({comp_reason})",
        f"Client quality: {client_score}/100 ({client_reason})",
        f"Value: {value_score}/100 ({value_reason})",
        f"Timing: {timing_score}/100 ({timing_reason})",
        f"Complexity: {complexity}",
        f"Final score: {final_score}/100",
        f"Decision: {decision}",
        f"Proposal mode: {proposal_mode}",
        f"Auto apply: {'YES' if auto_apply else 'NO'}",
    ]

    if invites_sent >= 10 and unanswered_invites >= 7:
        reasons.append("Opportunity spike detected: high invite volume with weak response rate")
    elif invites_sent >= 5 and unanswered_invites >= 5:
        reasons.append("Opportunity spike detected: client outreach is underperforming")

    if recommended_bid > 0:
        reasons.append(
            f"Bid strategy: low ${bid_range['low']} | avg ${bid_range['avg']} | high ${bid_range['high']} | recommended ${recommended_bid}"
        )
    else:
        reasons.append(
            f"Bid strategy: low ${bid_range['low']} | avg ${bid_range['avg']} | high ${bid_range['high']} | recommended SKIP"
        )

    return WinProbabilityV2(
        skill_score=skill_score,
        competition_score=competition_score,
        client_score=client_score,
        value_score=value_score,
        timing_score=timing_score,
        final_score=final_score,
        decision=decision,
        recommended_bid=recommended_bid,
        bid_low=bid_range["low"],
        bid_avg=bid_range["avg"],
        bid_high=bid_range["high"],
        complexity=complexity,
        proposal_mode=proposal_mode,
        auto_apply=auto_apply,
        reasons=reasons,
    )


def build_auto_apply_payload(
    text: str,
    proposals: str,
    last_viewed: str,
    interviewing: int,
    invites_sent: int,
    unanswered_invites: int,
    client_budget: Optional[int] = None,
    hires: int = 0,
    total_spent: int = 0,
    payment_verified: bool = False,
) -> dict:
    v2 = calculate_win_probability_v2(
        text=text,
        proposals=proposals,
        last_viewed=last_viewed,
        interviewing=interviewing,
        invites_sent=invites_sent,
        unanswered_invites=unanswered_invites,
        client_budget=client_budget,
        hires=hires,
        total_spent=total_spent,
        payment_verified=payment_verified,
    )

    return {
        "auto_apply": v2.auto_apply,
        "decision": v2.decision,
        "proposal_mode": v2.proposal_mode,
        "recommended_bid": v2.recommended_bid,
        "bid_range": {
            "low": v2.bid_low,
            "avg": v2.bid_avg,
            "high": v2.bid_high,
        },
        "win_score": v2.final_score,
        "complexity": v2.complexity,
        "reasons": v2.reasons,
    }


def should_generate_proposal_from_payload(payload: dict) -> bool:
    return payload.get("proposal_mode") in {"premium", "standard"}


def should_submit_proposal_from_payload(payload: dict) -> bool:
    return bool(payload.get("auto_apply", False))


class JobScorer:
    """
    Compatibility wrapper for the existing app architecture.

    streamlit_app.py expects:
        scorer = JobScorer()
        scorer.score(job_text=..., classification=..., profile=..., past_projects=...)
    """

    def score(
        self,
        job_text: str,
        classification: dict | None = None,
        profile: dict | None = None,
        past_projects: list | None = None,
    ) -> dict:
        classification = classification or {}
        profile = profile or {}
        past_projects = past_projects or []

        base = score_job(job_text)

        matched_categories = base.matched_categories
        matched_keywords = base.matched_keywords

        technical_fit = min(10, max(0, len(matched_categories) * 2))
        if any(cat in matched_categories for cat in ["scraping", "automation", "apify", "python_backend"]):
            technical_fit = min(10, technical_fit + 2)

        project_text = " ".join(
            [
                str(profile),
                " ".join(str(p) for p in past_projects),
                " ".join(matched_categories),
                " ".join(k for vals in matched_keywords.values() for k in vals),
            ]
        ).lower()

        proof_signals = [
            "apify",
            "playwright",
            "crawlee",
            "streamlit",
            "fastapi",
            "scraping",
            "automation",
            "lead generation",
            "polymarket",
            "prediction market",
        ]
        proof_fit = min(10, sum(1 for s in proof_signals if s in project_text))

        text_lower = normalize_text(job_text)
        clarity_terms = [
            "requirements",
            "deliverables",
            "scope",
            "budget",
            "timeline",
            "what we want",
            "to apply",
            "responsibilities",
            "must",
            "technical requirements",
        ]
        client_clarity = min(10, sum(1 for t in clarity_terms if t in text_lower))

        complexity = detect_complexity(job_text)
        bid_range = estimate_bid_range(job_text, None)

        if complexity == "high":
            budget_quality = 7
        elif complexity == "medium":
            budget_quality = 6
        else:
            budget_quality = 5

        execution_risk = 3
        if "api" in text_lower or "fastapi" in text_lower:
            execution_risk += 1
        if "playwright" in text_lower or "crawlee" in text_lower or "apify" in text_lower:
            execution_risk += 2
        if "bot" in text_lower or "automation engine" in text_lower or "scalable" in text_lower:
            execution_risk += 2
        execution_risk = min(10, execution_risk)

        total = technical_fit + proof_fit + client_clarity + budget_quality - execution_risk
        total = max(0, min(30, total))

        if total >= 22:
            fit = "strong"
            decision = "apply"
        elif total >= 16:
            fit = "moderate"
            decision = "selective"
        else:
            fit = "weak"
            decision = "skip"

        risk_flags = []
        if base.weak_signals_found:
            risk_flags.append(f"Weak-fit signals: {', '.join(base.weak_signals_found)}")
        if base.exclusion_signals_found:
            risk_flags.append(f"Exclusion signals: {', '.join(base.exclusion_signals_found)}")
        if execution_risk >= 7:
            risk_flags.append("High execution complexity")
        if client_clarity <= 2:
            risk_flags.append("Client scope is vague")

        return {
            "fit": fit,
            "decision": decision,
            "scores": {
                "technical_fit": technical_fit,
                "proof_fit": proof_fit,
                "client_clarity": client_clarity,
                "budget_quality": budget_quality,
                "execution_risk": execution_risk,
                "total": total,
            },
            "risk_flags": risk_flags,
            "matched_categories": matched_categories,
            "matched_keywords": matched_keywords,
            "base_score": base.score,
            "base_recommendation": base.recommendation,
            "complexity": complexity,
            "estimated_bid_range": bid_range,
            "reasons": base.reasons,
        }
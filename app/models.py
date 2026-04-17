from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Literal


DecisionType = Literal[
    "STRONG_APPLY",
    "APPLY",
    "CONDITIONAL_APPLY",
    "SKIP",
]

ProposalMode = Literal[
    "PREMIUM",
    "STANDARD",
    "NONE",
]

ConfidenceLabel = Literal[
    "HIGH",
    "MEDIUM",
    "LOW",
]


@dataclass
class JobInput:
    title: str = ""
    description: str = ""
    category: str = ""
    payment_verified: bool = False
    budget_type: str = ""   # fixed / hourly / unknown
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    hourly_min: Optional[float] = None
    hourly_max: Optional[float] = None

    proposals_count: Optional[int] = None
    interviewing_count: Optional[int] = None
    invites_sent: Optional[int] = None
    unanswered_invites: Optional[int] = None
    last_viewed_hours_ago: Optional[float] = None

    client_hire_rate: Optional[float] = None
    client_total_spent: Optional[float] = None
    client_reviews_count: Optional[int] = None
    client_avg_hourly_rate: Optional[float] = None
    client_location: str = ""

    user_profile_tags: List[str] = field(default_factory=list)


@dataclass
class ParsedSignals:
    mentions_scraping: bool = False
    mentions_automation: bool = False
    mentions_apify: bool = False
    mentions_large_dataset: bool = False
    mentions_images: bool = False
    mentions_csv: bool = False
    mentions_excel: bool = False
    mentions_json: bool = False
    mentions_api: bool = False
    mentions_anti_bot: bool = False
    mentions_browser_automation: bool = False

    mentions_target_website: bool = False
    mentions_output_format: bool = False
    mentions_deliverables: bool = False
    mentions_scale: bool = False

    clarity_score: int = 0
    execution_risk_score: int = 0
    technical_fit_score: int = 0
    category_fit_score: int = 0


@dataclass
class GateResult:
    passed: bool
    reasons: List[str] = field(default_factory=list)


@dataclass
class ScoreBreakdown:
    technical_fit: int = 0
    client_quality: int = 0
    competition_risk: int = 0
    value: int = 0
    timing: int = 0
    clarity: int = 0
    execution_risk: int = 0
    confidence: int = 0
    final_score: int = 0


@dataclass
class ActionPlan:
    proposal_mode: ProposalMode = "NONE"
    should_boost: bool = False
    auto_apply: bool = False
    pricing_mode: str = "NONE"
    bid_low: Optional[float] = None
    bid_mid: Optional[float] = None
    bid_high: Optional[float] = None


@dataclass
class EvaluationResult:
    gate: GateResult
    scores: ScoreBreakdown
    decision: DecisionType
    confidence_label: ConfidenceLabel
    reasons: List[str]
    risks: List[str]
    action: ActionPlan
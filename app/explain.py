from __future__ import annotations

from app.models import JobInput, ParsedSignals


def build_reasons(job, parsed, result):
    reasons = []

    # Fit
    if result.scores.technical_fit >= 70:
        reasons.append("Strong technical match for scraping/automation tasks.")
    elif result.scores.technical_fit >= 50:
        reasons.append("Moderate technical match.")

    # Client
    if result.scores.client_quality >= 70:
        reasons.append("Client appears reliable with good history.")

    # Competition
    if result.scores.competition_risk <= 40:
        reasons.append("Low competition — higher chance of being noticed.")

    # Timing
    if result.scores.timing >= 75:
        reasons.append("Timing is favorable — early application advantage.")

    # Decision summary
    if result.decision == "APPLY":
        reasons.append("Solid opportunity — consider clarifying requirements early.")
    elif result.decision == "CONDITIONAL_APPLY":
        reasons.append("Apply selectively — not a high-confidence opportunity.")
    elif result.decision == "STRONG_APPLY":
        reasons.append("Strong opportunity — prioritize this job.")

    return reasons


def build_risks(job, parsed, result):
    risks = []

    # 🔴 Hard risks
    if result.scores.competition_risk >= 70:
        risks.append("High competition — many applicants.")

    if result.scores.client_quality < 45:
        risks.append("Low-quality client — potential payment or communication risk.")

    if result.scores.execution_risk >= 60:
        risks.append("Technically complex — risk of delays or blockers.")

    # 🟡 Soft risks (uncertainty)
    if result.scores.clarity < 45:
        risks.append("Limited job detail — scope may be unclear.")

    if not parsed.mentions_target_website:
        risks.append("Target website not specified.")

    if not parsed.mentions_output_format:
        risks.append("Output format not clearly defined.")

    # 🟢 Fallback (always show something)
    if not risks:
        if result.scores.final_score >= 70:
            risks.append("Low-risk opportunity.")
        else:
            risks.append("Some uncertainty remains despite overall good signals.")

    return risks
from __future__ import annotations

from app.models import JobInput, ParsedSignals, GateResult


def run_gate(job: JobInput, parsed: ParsedSignals) -> GateResult:
    reasons: list[str] = []

    if not job.payment_verified:
        reasons.append("Client payment is not verified.")

    if job.proposals_count is not None and job.proposals_count >= 50:
        reasons.append("Proposal count is too high.")

    if job.client_hire_rate is not None and job.client_hire_rate < 20:
        reasons.append("Client hire rate is too low.")

    if job.budget_min is not None and job.budget_min < 100:
        reasons.append("Budget appears too low.")

    if parsed.clarity_score < 20:
        reasons.append("Job description is too vague.")

    if parsed.category_fit_score < 40:
        reasons.append("Weak category fit.")

    return GateResult(
        passed=len(reasons) == 0,
        reasons=reasons,
    )
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from classifier import JobClassifier
from profile_store import load_past_projects, load_profile
from proposal_writer import ProposalWriter
from scoring import score_job
from strategy import JobStrategy

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_EVAL_DIR = BASE_DIR / "outputs" / "evaluations"
OUTPUT_PROPOSAL_DIR = BASE_DIR / "outputs" / "proposals"

OUTPUT_EVAL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PROPOSAL_DIR.mkdir(parents=True, exist_ok=True)


class ProposalBot:
    def __init__(self) -> None:
        self.profile = load_profile()
        self.past_projects = load_past_projects()
        self.classifier = JobClassifier()
        self.writer = ProposalWriter()
        self.strategy = JobStrategy()

    def suggest_pricing(self, recommendation: str, job_meta: dict | None = None) -> dict:
        job_meta = job_meta or {}

        if recommendation == "premium":
            return {
                "pricing_tier": "premium",
                "hourly_range": "$80-$120/hr",
                "fixed_price_range": "$300-$1200",
                "bid_note": "Strong match. Position as specialist and lead with proof."
            }

        if recommendation == "standard":
            return {
                "pricing_tier": "standard",
                "hourly_range": "$50-$80/hr",
                "fixed_price_range": "$150-$500",
                "bid_note": "Good fit. Competitive but still value-based."
            }

        return {
            "pricing_tier": "skip",
            "hourly_range": "N/A",
            "fixed_price_range": "N/A",
            "bid_note": "Low-fit job. Protect ROI and skip."
        }

    def evaluate_job(self, job_text: str, job_meta: dict | None = None) -> dict:
        job_meta = job_meta or {}

        classification = self.classifier.classify(job_text)
        scoring_result = score_job(job_text)

        evaluation = {
            "fit": scoring_result.recommendation,
            "decision": "APPLY" if scoring_result.recommendation != "skip" else "SKIP",
            "matched_categories": scoring_result.matched_categories,
            "matched_keywords": scoring_result.matched_keywords,
            "weak_signals_found": scoring_result.weak_signals_found,
            "exclusion_signals_found": scoring_result.exclusion_signals_found,
            "reasons": scoring_result.reasons,
            "scores": {
                "total": scoring_result.score,
                "keyword_fit": scoring_result.score,
                "technical_fit": scoring_result.score,
                "proof_fit": 0,
                "client_clarity": 0,
                "budget_quality": 0,
                "execution_risk": 0,
            },
            "risk_flags": scoring_result.weak_signals_found + scoring_result.exclusion_signals_found,
        }

        strategy_input = {
            "fit": evaluation["fit"],
            "decision": evaluation["decision"],
            "scores": evaluation["scores"],
            "risk_flags": evaluation["risk_flags"],
        }

        try:
            strategy = self.strategy.decide(strategy_input, job_meta)
        except Exception:
            proposal_type = (
                "premium"
                if scoring_result.recommendation == "premium"
                else "standard"
                if scoring_result.recommendation == "standard"
                else "short"
            )
            strategy = {
                "proposal_type": proposal_type,
                "recommendation": scoring_result.recommendation,
            }

        short_proposal = self.writer.write_short(
            self.profile,
            job_text,
            self.past_projects,
        )
        standard_proposal = self.writer.write_standard(
            self.profile,
            job_text,
            self.past_projects,
        )
        premium_proposal = self.writer.write_premium(
            self.profile,
            job_text,
            self.past_projects,
        )

        proposal_type = strategy.get("proposal_type", "standard")
        if scoring_result.recommendation == "skip":
            proposal_type = "skip"

        selected_proposal = self.writer.write_selected(
            self.profile,
            job_text,
            self.past_projects,
            mode=proposal_type,
        )
        pricing = self.suggest_pricing(scoring_result.recommendation, job_meta)
        return {
            "timestamp": datetime.now().isoformat(),
            "classification": classification,
            "evaluation": evaluation,
            "strategy": strategy,
            "pricing": pricing,
            "selected_proposal": selected_proposal,
            "short_proposal": short_proposal,
            "standard_proposal": standard_proposal,
            "premium_proposal": premium_proposal,
        }

    def save_results(self, result: dict) -> tuple[Path, Path]:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        eval_path = OUTPUT_EVAL_DIR / f"evaluation_{stamp}.json"
        proposal_path = OUTPUT_PROPOSAL_DIR / f"proposal_{stamp}.txt"

        with eval_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        proposal_text = (
            "=== SELECTED PROPOSAL ===\n\n"
            + result["selected_proposal"]
            + "\n\n=== SHORT PROPOSAL ===\n\n"
            + result["short_proposal"]
            + "\n\n=== STANDARD PROPOSAL ===\n\n"
            + result["standard_proposal"]
            + "\n\n=== PREMIUM PROPOSAL ===\n\n"
            + result["premium_proposal"]
        )

        with proposal_path.open("w", encoding="utf-8") as f:
            f.write(proposal_text)


        return eval_path, proposal_path


def collect_job_meta() -> dict:
    def read_int(prompt: str, default: int = 0) -> int:
        raw = input(f"{prompt} [{default}]: ").strip()
        if not raw:
            return default
        try:
            return int(raw)
        except ValueError:
            print(f"Invalid number. Using default {default}.")
            return default

    print("\nEnter job market data (press Enter to use default value):")

    return {
        "proposals": read_int("Proposals", 0),
        "last_viewed_hours": read_int("Last viewed by client (hours ago)", 0),
        "interviewing": read_int("Interviewing", 0),
        "invites_sent": read_int("Invites sent", 0),
        "unanswered_invites": read_int("Unanswered invites", 0),
        "avg_bid": read_int("Average bid", 0),
        "high_bid": read_int("High bid", 0),
        "low_bid": read_int("Low bid", 0),
    }


def main() -> None:
    print("Upwork Proposal Bot")
    print("Paste the job description below. Finish with an empty line twice.\n")

    lines = []
    empty_count = 0

    while True:
        line = input()
        if line.strip() == "":
            empty_count += 1
            if empty_count >= 2:
                break
        else:
            empty_count = 0
        lines.append(line)

    job_text = "\n".join(lines).strip()

    if not job_text:
        print("No job text provided.")
        return

    bot = ProposalBot()
    job_meta = collect_job_meta()
    result = bot.evaluate_job(job_text, job_meta)

    eval_path, proposal_path = bot.save_results(result)
    scores = result["evaluation"]["scores"]

    print("\n=== JOB EVALUATION ===")
    print(f"Fit: {result['evaluation']['fit']}")
    print(f"Decision: {result['evaluation']['decision']}")
    print(f"Primary category: {result['classification'].get('primary_category', 'unknown')}")

    print("Scores:")
    print(f"- Total: {scores['total']}")
    print(f"- Technical fit: {scores.get('technical_fit', 0)}")
    print(f"- Proof fit: {scores.get('proof_fit', 0)}")
    print(f"- Client clarity: {scores.get('client_clarity', 0)}")
    print(f"- Budget quality: {scores.get('budget_quality', 0)}")
    print(f"- Execution risk: {scores.get('execution_risk', 0)}")

    print("\nMatched categories:")
    if result["evaluation"]["matched_categories"]:
        for category in result["evaluation"]["matched_categories"]:
            print(f"- {category}")
    else:
        print("- None")

    print("\nRisk flags:")
    if result["evaluation"]["risk_flags"]:
        for flag in result["evaluation"]["risk_flags"]:
            print(f"- {flag}")
    else:
        print("- None detected")

    print("\nReasons:")
    for reason in result["evaluation"]["reasons"]:
        print(f"- {reason}")

    print("\n=== SELECTED PROPOSAL ===\n")
    print(result["selected_proposal"])

    print("\n=== SHORT PROPOSAL ===\n")
    print(result["short_proposal"])

    print("\n=== STANDARD PROPOSAL ===\n")
    print(result["standard_proposal"])

    print("\n=== PREMIUM PROPOSAL ===\n")
    print(result["premium_proposal"])

    print(f"\nSaved evaluation to: {eval_path}")
    print(f"Saved proposals to: {proposal_path}")


if __name__ == "__main__":
    main()
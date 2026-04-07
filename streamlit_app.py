from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from classifier import JobClassifier
from profile_store import load_past_projects, load_profile
from proposal_writer import ProposalWriter
from strategy import JobStrategy

# IMPORTANT:
# This assumes your updated scoring.py now includes:
# - JobScorer
# - calculate_win_probability_v2
# - build_auto_apply_payload
from scoring import JobScorer, calculate_win_probability_v2, build_auto_apply_payload


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
        self.scorer = JobScorer()
        self.writer = ProposalWriter()
        self.strategy = JobStrategy()

    def evaluate_job(self, job_text: str, job_meta: dict[str, Any] | None = None) -> dict[str, Any]:
        classification = self.classifier.classify(job_text)
        scoring = self.scorer.score(
            job_text=job_text,
            classification=classification,
            profile=self.profile,
            past_projects=self.past_projects,
        )

        job_meta = job_meta or {}
        strategy = self.strategy.decide(scoring, job_meta)

        proposals_label = job_meta.get("proposals_label", "0")
        last_viewed_label = job_meta.get("last_viewed_label", "today")
        interviewing = int(job_meta.get("interviewing", 0))
        invites_sent = int(job_meta.get("invites_sent", 0))
        unanswered_invites = int(job_meta.get("unanswered_invites", 0))
        client_budget = int(job_meta.get("avg_bid", 0) or 0)
        hires = int(job_meta.get("hires", 0))
        total_spent = int(job_meta.get("total_spent", 0))
        payment_verified = bool(job_meta.get("payment_verified", False))

        win_v2 = calculate_win_probability_v2(
            text=job_text,
            proposals=proposals_label,
            last_viewed=last_viewed_label,
            interviewing=interviewing,
            invites_sent=invites_sent,
            unanswered_invites=unanswered_invites,
            client_budget=client_budget,
            hires=hires,
            total_spent=total_spent,
            payment_verified=payment_verified,
        )

        auto_apply_payload = build_auto_apply_payload(
            text=job_text,
            proposals=proposals_label,
            last_viewed=last_viewed_label,
            interviewing=interviewing,
            invites_sent=invites_sent,
            unanswered_invites=unanswered_invites,
            client_budget=client_budget,
            hires=hires,
            total_spent=total_spent,
            payment_verified=payment_verified,
        )

        short_proposal = self.writer.write_short(self.profile, job_text, self.past_projects)
        standard_proposal = self.writer.write_standard(self.profile, job_text, self.past_projects)
        premium_proposal = self.writer.write_premium(self.profile, job_text, self.past_projects)

        v2_mode = win_v2.proposal_mode
        strategy_proposal_type = strategy.get("proposal_type", "standard")

        if v2_mode == "premium":
            selected_proposal = premium_proposal
            selected_type = "premium"
        elif v2_mode == "standard":
            selected_proposal = standard_proposal
            selected_type = "standard"
        elif strategy_proposal_type == "short":
            selected_proposal = short_proposal
            selected_type = "short"
        elif strategy_proposal_type == "premium":
            selected_proposal = premium_proposal
            selected_type = "premium"
        else:
            selected_proposal = standard_proposal
            selected_type = "standard"

        return {
            "timestamp": datetime.now().isoformat(),
            "classification": classification,
            "evaluation": scoring,
            "strategy": strategy,
            "win_v2": win_v2.to_dict(),
            "auto_apply_payload": auto_apply_payload,
            "selected_type": selected_type,
            "selected_proposal": selected_proposal,
            "short_proposal": short_proposal,
            "standard_proposal": standard_proposal,
            "premium_proposal": premium_proposal,
        }

    def save_results(self, result: dict[str, Any]) -> tuple[Path, Path]:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        eval_path = OUTPUT_EVAL_DIR / f"evaluation_{stamp}.json"
        proposal_path = OUTPUT_PROPOSAL_DIR / f"proposal_{stamp}.txt"

        with eval_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        proposal_text = (
            f"=== SELECTED PROPOSAL ({result.get('selected_type', 'standard').upper()}) ===\n\n"
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


@st.cache_resource
def get_bot() -> ProposalBot:
    return ProposalBot()


def init_state() -> None:
    if "result" not in st.session_state:
        st.session_state.result = None
    if "eval_path" not in st.session_state:
        st.session_state.eval_path = None
    if "proposal_path" not in st.session_state:
        st.session_state.proposal_path = None


def metric_card(label: str, value: Any) -> None:
    st.metric(label, value)


def render_scores(scores: dict[str, Any]) -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Technical Fit", scores.get("technical_fit", 0))
        metric_card("Proof Fit", scores.get("proof_fit", 0))
    with c2:
        metric_card("Client Clarity", scores.get("client_clarity", 0))
        metric_card("Budget Quality", scores.get("budget_quality", 0))
    with c3:
        metric_card("Execution Risk", scores.get("execution_risk", 0))
        metric_card("Total Score", scores.get("total", 0))


def proposals_to_label(proposals: int) -> str:
    if proposals <= 0:
        return "0"
    if proposals < 5:
        return "Less than 5"
    if proposals <= 10:
        return "5 to 10"
    if proposals <= 15:
        return "10 to 15"
    if proposals <= 20:
        return "15 to 20"
    if proposals <= 50:
        return "20 to 50"
    return "50+"


def hours_to_last_viewed_label(last_viewed_hours: int) -> str:
    if last_viewed_hours <= 0:
        return "just now"
    if last_viewed_hours <= 24:
        return "today"
    if last_viewed_hours <= 48:
        return "yesterday"
    if last_viewed_hours <= 72:
        return "2 to 3 days ago"
    if last_viewed_hours <= 168:
        return "4 to 7 days ago"
    return "more than 1 week ago"


def build_market_meta(
    proposals: int,
    last_viewed_hours: int,
    interviewing: int,
    invites_sent: int,
    unanswered_invites: int,
    avg_bid: int,
    high_bid: int,
    low_bid: int,
    hires: int,
    total_spent: int,
    payment_verified: bool,
) -> dict[str, Any]:
    return {
        "proposals": proposals,
        "proposals_label": proposals_to_label(proposals),
        "last_viewed_hours": last_viewed_hours,
        "last_viewed_label": hours_to_last_viewed_label(last_viewed_hours),
        "interviewing": interviewing,
        "invites_sent": invites_sent,
        "unanswered_invites": unanswered_invites,
        "avg_bid": avg_bid,
        "high_bid": high_bid,
        "low_bid": low_bid,
        "hires": hires,
        "total_spent": total_spent,
        "payment_verified": payment_verified,
    }


def render_v2_panel(win_v2: dict[str, Any]) -> None:
    st.subheader("🚀 Win Probability V2")

    a, b, c, d = st.columns(4)
    with a:
        st.metric("Final Score", f"{win_v2.get('final_score', 0)}/100")
    with b:
        st.metric("Decision", win_v2.get("decision", "-"))
    with c:
        st.metric("Proposal Mode", str(win_v2.get("proposal_mode", "-")).title())
    with d:
        st.metric("Auto Apply", "Yes" if win_v2.get("auto_apply") else "No")

    st.write(f"**Complexity:** {str(win_v2.get('complexity', '-')).title()}")
    st.caption(
        "V2 weighs skill fit, competition, client quality, value, timing, and opportunity signals."
    )

    st.subheader("📊 V2 Breakdown")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Skill", win_v2.get("skill_score", 0))
    with c2:
        st.metric("Competition", win_v2.get("competition_score", 0))
    with c3:
        st.metric("Client", win_v2.get("client_score", 0))
    with c4:
        st.metric("Value", win_v2.get("value_score", 0))
    with c5:
        st.metric("Timing", win_v2.get("timing_score", 0))

    st.subheader("💰 Bid Strategy")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Low Bid", f"${win_v2.get('bid_low', 0)}")
    with c2:
        st.metric("Avg Bid", f"${win_v2.get('bid_avg', 0)}")
    with c3:
        st.metric("High Bid", f"${win_v2.get('bid_high', 0)}")
    with c4:
        recommended_bid = win_v2.get("recommended_bid", 0)
        st.metric("Recommended", "Skip" if recommended_bid <= 0 else f"${recommended_bid}")

    st.subheader("🧠 Reasons")
    for r in win_v2.get("reasons", []):
        st.write(f"- {r}")


def main() -> None:
    st.set_page_config(page_title="Upwork Proposal Engine", page_icon="⚡", layout="wide")
    init_state()

    st.title("⚡ Upwork Proposal Engine")
    st.caption("Evaluate a job, score win probability, choose the right proposal mode, and generate a ready-to-use application.")

    bot = get_bot()

    with st.sidebar:
        st.subheader("Market Signals")
        proposals = st.number_input("Proposals", min_value=0, value=0, step=1)
        last_viewed_hours = st.number_input("Last viewed by client (hours ago)", min_value=0, value=0, step=1)
        interviewing = st.number_input("Interviewing", min_value=0, value=0, step=1)
        invites_sent = st.number_input("Invites sent by client", min_value=0, value=0, step=1)
        unanswered_invites = st.number_input("Unanswered invites from freelancers", min_value=0, value=0, step=1)

        st.caption(
            "How the engine interprets these:\n"
            "• More proposals → more competition\n"
            "• More interviewing → later-stage competition\n"
            "• More invites sent → slight negative (client is mass outreaching)\n"
            "• More unanswered invites → positive opportunity signal\n"
            "• High invites + high unanswered → opportunity spike"
        )

        st.divider()
        st.subheader("Bid Evaluation")
        avg_bid = st.number_input("Average bid", min_value=0, value=0, step=1)
        high_bid = st.number_input("High bid", min_value=0, value=0, step=1)
        low_bid = st.number_input("Low bid", min_value=0, value=0, step=1)

        st.caption(
            "Average bid is used as the main budget signal for pricing guidance and recommended bid."
        )

        st.divider()
        st.subheader("Client Quality")
        hires = st.number_input("Client hires", min_value=0, value=0, step=1)
        total_spent = st.number_input("Client total spent ($)", min_value=0, value=0, step=100)
        payment_verified = st.checkbox("Payment verified", value=False)

        st.divider()
        st.subheader("Quick Notes")
        st.markdown(
            "- Higher competition reduces win probability.\n"
            "- Interviewing is treated as late-stage competition.\n"
            "- Invites sent are mildly negative unless unanswered invites are also high.\n"
            "- Unanswered invites increase opportunity score.\n"
            "- V2 proposal mode overrides the old proposal selector.\n"
            "- Auto-apply only triggers on strong-fit, high-score jobs."
        )

        with st.expander("ℹ️ Signal Examples"):
            st.markdown(
                "**Example 1:** Less than 5 proposals + viewed today + 0 interviewing → strong target\n\n"
                "**Example 2:** 20 invites sent + 18 unanswered → good opportunity spike\n\n"
                "**Example 3:** 5 interviewing + 20 to 50 proposals → high competition, weaker target"
            )

    default_job_text = """Paste the Upwork job description here..."""
    job_text = st.text_area("Job Description", value=default_job_text, height=320)

    cta1, cta2 = st.columns([1, 1])
    with cta1:
        run_clicked = st.button("Generate Proposal", use_container_width=True, type="primary")
    with cta2:
        clear_clicked = st.button("Clear Results", use_container_width=True)

    if clear_clicked:
        st.session_state.result = None
        st.session_state.eval_path = None
        st.session_state.proposal_path = None
        st.rerun()

    if run_clicked:
        clean_text = job_text.strip()
        if not clean_text or clean_text == default_job_text:
            st.warning("Paste a real job description first.")
        else:
            meta = build_market_meta(
                proposals=proposals,
                last_viewed_hours=last_viewed_hours,
                interviewing=interviewing,
                invites_sent=invites_sent,
                unanswered_invites=unanswered_invites,
                avg_bid=avg_bid,
                high_bid=high_bid,
                low_bid=low_bid,
                hires=hires,
                total_spent=total_spent,
                payment_verified=payment_verified,
            )

            result = bot.evaluate_job(clean_text, meta)
            eval_path, proposal_path = bot.save_results(result)
            st.session_state.result = result
            st.session_state.eval_path = eval_path
            st.session_state.proposal_path = proposal_path

    result = st.session_state.result
    if not result:
        st.info("Paste a job, set the market signals in the sidebar, then click Generate Proposal.")
        return

    evaluation = result["evaluation"]
    strategy = result["strategy"]
    classification = result["classification"]
    win_v2 = result.get("win_v2", {})
    auto_apply_payload = result.get("auto_apply_payload", {})

    top1, top2, top3, top4 = st.columns(4)
    with top1:
        st.metric("Fit", evaluation.get("fit", "-"))
    with top2:
        st.metric("Decision", win_v2.get("decision", evaluation.get("decision", "-")))
    with top3:
        st.metric("Proposal Type", str(result.get("selected_type", strategy.get("proposal_type", "standard"))).title())
    with top4:
        st.metric("Primary Category", classification.get("primary_category", "general"))

    st.subheader("Scorecard")
    render_scores(evaluation.get("scores", {}))

    st.divider()
    render_v2_panel(win_v2)

    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Strategy")
        st.write(f"**Decision:** {strategy.get('decision', '-')}")
        st.write(f"**Positioning:** {strategy.get('positioning', '-')}")
        st.write(f"**Effort Level:** {strategy.get('effort', '-')}")
        st.write(f"**Why:** {strategy.get('strategy_note', '-')}")

        risk_flags = evaluation.get("risk_flags", [])
        st.subheader("Risk Flags")
        if risk_flags:
            for flag in risk_flags:
                st.write(f"- {flag}")
        else:
            st.write("No risk flags detected.")

    with right:
        st.subheader("Matched Keywords")
        matched_keywords = classification.get("matched_keywords", [])
        if matched_keywords:
            st.write(", ".join(matched_keywords))
        else:
            st.write("No strong keywords matched.")

        st.subheader("Matched Categories")
        matched_categories = classification.get("matched_categories", {})
        if matched_categories:
            st.json(matched_categories)
        else:
            st.write("No category weighting available.")

    st.divider()
    st.subheader("🤖 Auto-Apply Engine")
    c1, c2 = st.columns(2)
    with c1:
        if auto_apply_payload.get("auto_apply"):
            st.success("Auto-submit proposal: YES")
        else:
            st.info("Auto-submit proposal: NO")
    with c2:
        proposal_mode = auto_apply_payload.get("proposal_mode", "skip")
        if proposal_mode in {"premium", "standard"}:
            st.success(f"Generate proposal: {proposal_mode.upper()}")
        elif proposal_mode == "shortlist_only":
            st.warning("Generate proposal: REVIEW MANUALLY")
        else:
            st.info("Generate proposal: SKIP")

    with st.expander("View Auto-Apply Payload"):
        st.json(auto_apply_payload)

    st.divider()
    st.subheader("Selected Proposal")
    st.text_area("Use this version", value=result["selected_proposal"], height=260)
    st.download_button(
        label="Download Selected Proposal (.txt)",
        data=result["selected_proposal"],
        file_name="selected_proposal.txt",
        mime="text/plain",
    )

    tab1, tab2, tab3, tab4 = st.tabs(["Short", "Standard", "Premium", "Saved Files"])

    with tab1:
        st.text_area("Short Proposal", value=result["short_proposal"], height=260)
    with tab2:
        st.text_area("Standard Proposal", value=result["standard_proposal"], height=360)
    with tab3:
        st.text_area("Premium Proposal", value=result["premium_proposal"], height=420)
    with tab4:
        st.write(f"Evaluation JSON: {st.session_state.eval_path}")
        st.write(f"Proposal TXT: {st.session_state.proposal_path}")
        st.download_button(
            label="Download Evaluation JSON",
            data=json.dumps(result, indent=2, ensure_ascii=False),
            file_name="evaluation.json",
            mime="application/json",
        )


if __name__ == "__main__":
    main()
from __future__ import annotations

import streamlit as st

from profile_store import load_past_projects, load_profile
from proposal_writer import ProposalWriter
from scoring import score_job, adjust_score_with_activity, classify_job_fit


def suggest_pricing(recommendation: str) -> dict:
    if recommendation == "premium":
        return {
            "pricing_tier": "premium",
            "hourly_range": "$80–120/hr",
            "fixed_price_range": "$300–1200",
            "bid_note": "Strong match. Position as specialist.",
        }
    if recommendation == "standard":
        return {
            "pricing_tier": "standard",
            "hourly_range": "$50–80/hr",
            "fixed_price_range": "$150–500",
            "bid_note": "Good fit. Competitive but value-based.",
        }
    return {
        "pricing_tier": "skip",
        "hourly_range": "N/A",
        "fixed_price_range": "N/A",
        "bid_note": "Low-fit job. Skip.",
    }


st.set_page_config(page_title="Upwork Proposal Engine", layout="wide")

# =========================
# Sidebar
# =========================
st.sidebar.title("⚙️ Settings")

show_reasons = st.sidebar.checkbox("Show scoring reasons", value=True)
show_pricing = st.sidebar.checkbox("Show pricing guidance", value=True)
show_short = st.sidebar.checkbox("Show short proposal", value=True)
show_standard = st.sidebar.checkbox("Show standard proposal", value=True)
show_premium = st.sidebar.checkbox("Show premium proposal", value=True)

st.sidebar.divider()
st.sidebar.subheader("📊 Activity on This Job")

proposals = st.sidebar.selectbox(
    "Proposals",
    ["Less than 5", "5 to 10", "10 to 15", "15 to 20", "20 to 50", "50+"],
    index=4,
)

last_viewed = st.sidebar.selectbox(
    "Last viewed by client",
    ["just now", "today", "yesterday", "2 to 3 days ago", "4 to 7 days ago", "more than 1 week ago"],
    index=2,
)

interviewing = st.sidebar.number_input(
    "Interviewing",
    min_value=0,
    max_value=50,
    value=0,
)

invites_sent = st.sidebar.number_input(
    "Invites sent",
    min_value=0,
    max_value=50,
    value=0,
)

unanswered_invites = st.sidebar.number_input(
    "Unanswered invites",
    min_value=0,
    max_value=50,
    value=0,
)

# =========================
# Load profile data
# =========================
profile = load_profile()
past_projects = load_past_projects()
writer = ProposalWriter()

# =========================
# Main UI
# =========================
st.title("Upwork Proposal Engine")
st.caption("Paste an Upwork job post to score it and generate proposal versions.")

job_text = st.text_area("Paste Upwork job post", height=260)

if job_text.strip():
    result = score_job(job_text)

    # Apply job-activity adjustment
    adjusted_score, activity_reasons = adjust_score_with_activity(
        result.score,
        proposals,
        last_viewed,
        interviewing,
        invites_sent,
        unanswered_invites,
    )

    result.score = adjusted_score
    result.reasons.extend(activity_reasons)
    result.recommendation = classify_job_fit(result.score)

    pricing = suggest_pricing(result.recommendation)

    if result.recommendation == "skip":
        proposal_mode = "skip"
    elif result.recommendation == "premium":
        proposal_mode = "premium"
    else:
        proposal_mode = "standard"

    selected_proposal = writer.write_selected(
        profile,
        job_text,
        past_projects,
        mode=proposal_mode,
    )

    short_proposal = writer.write_short(profile, job_text, past_projects)
    standard_proposal = writer.write_standard(profile, job_text, past_projects)
    premium_proposal = writer.write_premium(profile, job_text, past_projects)

    if show_pricing:
        st.subheader("💰 Pricing Guidance")
        col1, col2, col3 = st.columns(3)
        col1.metric("Tier", pricing["pricing_tier"])
        col2.metric("Hourly", pricing["hourly_range"])
        col3.metric("Fixed", pricing["fixed_price_range"])
        st.caption(pricing["bid_note"])

    st.subheader("📊 Job Fit Analysis")
    col1, col2 = st.columns(2)
    col1.metric("Job Score", result.score)
    col2.metric("Recommendation", result.recommendation.upper())

    if result.matched_categories:
        st.write("**Matched categories:**", ", ".join(result.matched_categories))

    st.write("**Activity inputs used:**")
    st.write(
        f"- Proposals: {proposals}\n"
        f"- Last viewed by client: {last_viewed}\n"
        f"- Interviewing: {interviewing}\n"
        f"- Invites sent: {invites_sent}\n"
        f"- Unanswered invites: {unanswered_invites}"
    )

    if result.weak_signals_found:
        st.warning("Weak signals: " + ", ".join(result.weak_signals_found))

    if result.exclusion_signals_found:
        st.error("Exclusion signals: " + ", ".join(result.exclusion_signals_found))

    if show_reasons:
        with st.expander("🧠 Why this score"):
            for reason in result.reasons:
                st.write(f"- {reason}")

    st.subheader("✅ Selected Proposal")
    st.text_area("Selected Proposal", selected_proposal, height=220)

    if show_short:
        st.subheader("Short Proposal")
        st.text_area("Short Proposal", short_proposal, height=220)

    if show_standard:
        st.subheader("Standard Proposal")
        st.text_area("Standard Proposal", standard_proposal, height=320)

    if show_premium:
        st.subheader("Premium Proposal")
        st.text_area("Premium Proposal", premium_proposal, height=420)

else:
    st.info("Paste a job description to begin.")
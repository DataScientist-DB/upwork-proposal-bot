from __future__ import annotations

import streamlit as st

from app.engine import evaluate_job
from app.models import JobInput
from app.proposal_writer import ProposalWriter

proposal_writer = ProposalWriter()

st.set_page_config(
    page_title="Upwork Proposal Bot",
    page_icon="🎯",
    layout="wide",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2rem;
            max-width: 1260px;
        }

        .app-title {
            font-size: 2rem;
            font-weight: 800;
            color: #111827;
            margin-bottom: 0.2rem;
            line-height: 1.1;
        }

        .app-subtitle {
            font-size: 1rem;
            color: #6b7280;
            margin-bottom: 1.2rem;
        }

        .section-title {
            font-size: 1.12rem;
            font-weight: 700;
            color: #111827;
            margin-top: 0.3rem;
            margin-bottom: 0.75rem;
        }

        .soft-card {
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            padding: 16px 18px;
            background: linear-gradient(180deg, #ffffff 0%, #fafafa 100%);
            box-shadow: 0 6px 18px rgba(17, 24, 39, 0.05);
        }

        .pill {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
            background: #f3f4f6;
            color: #374151;
            margin-right: 6px;
            margin-bottom: 6px;
        }

        div[data-testid="stTabs"] button {
            font-weight: 600;
        }

        div[data-testid="stTextArea"] textarea {
            border-radius: 14px !important;
        }

        div[data-testid="stDownloadButton"] button,
        div[data-testid="stButton"] button {
            border-radius: 12px !important;
            font-weight: 600 !important;
        }

        div[data-testid="stSidebar"] .block-container {
            padding-top: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def proposal_band_to_count(band: str) -> int:
    mapping = {
        "Less than 5": 4,
        "5 to 10": 8,
        "10 to 20": 15,
        "20 to 50": 30,
        "50+": 55,
    }
    return mapping.get(band, 10)


def badge_color(decision: str) -> str:
    if decision == "STRONG_APPLY":
        return "#15803d"
    if decision == "APPLY":
        return "#2563eb"
    if decision == "CONDITIONAL_APPLY":
        return "#d97706"
    return "#b91c1c"


def confidence_color(label: str) -> str:
    if label == "HIGH":
        return "#15803d"
    if label == "MEDIUM":
        return "#d97706"
    return "#b91c1c"


def metric_color_by_score(value: int) -> str:
    if value >= 75:
        return "#15803d"
    if value >= 55:
        return "#d97706"
    return "#b91c1c"


def format_currency(value):
    if value is None:
        return "—"
    return f"${value:,.0f}"


def normalize_probability(result) -> int:
    value = getattr(result, "win_probability", None)
    if value is None:
        return 0
    try:
        return int(value)
    except Exception:
        return 0


def normalize_confidence_label(result) -> str:
    value = getattr(result, "confidence_label", None)
    if value:
        return str(value).upper()

    fallback = getattr(result, "confidence", None)
    if fallback:
        return str(fallback).upper()

    return "MEDIUM"


def normalize_proposal_mode(result) -> str:
    action = getattr(result, "action", None)
    if action and getattr(action, "proposal_mode", None):
        return str(action.proposal_mode).upper()

    value = getattr(result, "proposal_mode", None)
    if value:
        return str(value).upper()

    return "STANDARD"


def build_skills_list(category: str, title: str, description: str) -> list[str]:
    skills: list[str] = []

    if category and category.strip():
        skills.append(category.strip().title())

    text = f"{title} {description}".lower()

    keyword_map = {
        "python": "Python",
        "scrap": "Web Scraping",
        "selenium": "Selenium",
        "playwright": "Playwright",
        "beautifulsoup": "BeautifulSoup",
        "fastapi": "FastAPI",
        "api": "API Development",
        "streamlit": "Streamlit",
        "flask": "Flask",
        "automation": "Automation",
        "data extraction": "Data Extraction",
        "crawler": "Crawler Development",
        "dashboard": "Dashboard Development",
        "llm": "LLM",
        "gpt": "OpenAI / GPT",
        "rag": "RAG",
        "apify": "Apify",
    }

    for needle, label in keyword_map.items():
        if needle in text and label not in skills:
            skills.append(label)

    return skills


def render_metric_card(title: str, value: str, color: str = "#111827", subtitle: str = ""):
    subtitle_html = (
        f'<div style="font-size: 12px; color: #6b7280; margin-top: 8px; line-height: 1.45;">{subtitle}</div>'
        if subtitle
        else ""
    )

    st.markdown(
        f"""
        <div class="soft-card" style="height: 100%;">
            <div style="font-size: 12px; letter-spacing: 0.02em; text-transform: uppercase; color: #6b7280; margin-bottom: 10px;">
                {title}
            </div>
            <div style="font-size: 30px; font-weight: 800; color: {color}; line-height: 1.1;">
                {value}
            </div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_block(title: str, value: int, help_text: str = ""):
    safe_value = max(0, min(100, int(value)))
    st.markdown(f"**{title}**")
    st.progress(safe_value)
    st.caption(f"{safe_value}/100" + (f" · {help_text}" if help_text else ""))


def render_reason_list(title: str, items: list[str], empty_text: str):
    st.markdown(f"#### {title}")
    if items:
        for item in items:
            st.markdown(f"- {item}")
    else:
        st.caption(empty_text)


def proposal_filename(title: str, mode: str) -> str:
    safe_title = "".join(c if c.isalnum() or c in (" ", "_", "-") else "" for c in title).strip()
    safe_title = safe_title.replace(" ", "_") or "proposal"
    return f"{safe_title.lower()}_{mode.lower()}_proposal.txt"


# ============================================================
# HEADER
# ============================================================

st.markdown('<div class="app-title">🎯 Upwork Proposal Bot</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">Evaluate jobs, decide whether they are worth pursuing, and generate the right proposal strategy.</div>',
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("Job Inputs")
    st.markdown("### Setup")
    st.caption("Fill the job details, then run a full evaluation.")

    title = st.text_input("Job title", value="Web scraper needed")
    category = st.text_input("Category", value="scraping")

    description = st.text_area(
        "Job description",
        height=220,
        value=(
            "Extract product data including prices, descriptions, and images from a website. "
            "Need structured output for analysis."
        ),
    )

    st.markdown("---")
    st.subheader("Client")
    payment_verified = st.checkbox("Payment verified", value=True)
    client_hire_rate = st.number_input(
        "Client hire rate (%)",
        min_value=0.0,
        max_value=100.0,
        value=40.0,
        step=1.0,
        help="Percent of jobs where the client actually hired someone.",
    )
    client_total_spent = st.number_input(
        "Client total spent ($)",
        min_value=0.0,
        value=2000.0,
        step=100.0,
    )
    client_reviews_count = st.number_input(
        "Client reviews count",
        min_value=0,
        value=8,
        step=1,
    )
    client_avg_hourly_rate = st.number_input(
        "Client avg hourly rate ($)",
        min_value=0.0,
        value=35.0,
        step=1.0,
    )

    st.markdown("---")
    st.subheader("Competition / Timing")
    proposal_band = st.selectbox(
        "Number of proposals",
        options=["Less than 5", "5 to 10", "10 to 20", "20 to 50", "50+"],
        index=1,
    )
    interviewing_count = st.number_input("Interviewing count", min_value=0, value=0, step=1)
    invites_sent = st.number_input("Invites sent", min_value=0, value=0, step=1)
    unanswered_invites = st.number_input("Unanswered invites", min_value=0, value=0, step=1)
    last_viewed_hours_ago = st.number_input(
        "Client last viewed job (hours ago)",
        min_value=0.0,
        value=1.0,
        step=1.0,
    )

    st.markdown("---")
    st.subheader("Budget")
    budget_type = st.selectbox("Budget type", options=["fixed", "hourly", "unknown"], index=0)
    budget_min = st.number_input("Budget min ($)", min_value=0.0, value=400.0, step=50.0)
    budget_max = st.number_input("Budget max ($)", min_value=0.0, value=1000.0, step=50.0)
    hourly_min = st.number_input("Hourly min ($)", min_value=0.0, value=0.0, step=1.0)
    hourly_max = st.number_input("Hourly max ($)", min_value=0.0, value=0.0, step=1.0)

    evaluate = st.button("Evaluate Job", type="primary", use_container_width=True)


if not evaluate:
    st.info("Fill the inputs in the sidebar and click **Evaluate Job**.")
    st.stop()


# ============================================================
# BUILD INPUT MODEL
# ============================================================

job = JobInput(
    title=title,
    description=description,
    category=category,
    payment_verified=payment_verified,
    budget_type=budget_type,
    budget_min=budget_min if budget_min > 0 else None,
    budget_max=budget_max if budget_max > 0 else None,
    hourly_min=hourly_min if hourly_min > 0 else None,
    hourly_max=hourly_max if hourly_max > 0 else None,
    proposals_count=proposal_band_to_count(proposal_band),
    interviewing_count=interviewing_count,
    invites_sent=invites_sent,
    unanswered_invites=unanswered_invites,
    last_viewed_hours_ago=last_viewed_hours_ago,
    client_hire_rate=client_hire_rate,
    client_total_spent=client_total_spent,
    client_reviews_count=client_reviews_count,
    client_avg_hourly_rate=client_avg_hourly_rate,
)


# ============================================================
# EVALUATE
# ============================================================

result = evaluate_job(job)
win_probability = normalize_probability(result)
confidence_label = normalize_confidence_label(result)
proposal_mode = normalize_proposal_mode(result)

skills_list = build_skills_list(
    category=category,
    title=title,
    description=description,
)

proposal = proposal_writer.generate_from_fields(
    title=title,
    description=description,
    skills=skills_list,
    score=result.scores.final_score,
    win_probability=win_probability,
    confidence=confidence_label,
    proposal_mode=proposal_mode,
    reasons=result.reasons,
    risks=result.risks,
)


# ============================================================
# HERO SUMMARY
# ============================================================

st.markdown(
    f"""
    <div class="soft-card" style="margin-bottom: 16px;">
        <div style="display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap;">
            <div>
                <div style="font-size:13px; color:#6b7280; margin-bottom:6px;">Current job</div>
                <div style="font-size:24px; font-weight:800; color:#111827;">{title}</div>
                <div style="font-size:14px; color:#6b7280; margin-top:6px;">Category: {category or "—"}</div>
            </div>
            <div>
                <span class="pill">Decision: {result.decision}</span>
                <span class="pill">Proposal: {result.action.proposal_mode}</span>
                <span class="pill">Win Probability: {win_probability}%</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

summary_cols = st.columns(4)

with summary_cols[0]:
    render_metric_card(
        "Decision",
        result.decision,
        badge_color(result.decision),
        "Should you pursue this job?",
    )

with summary_cols[1]:
    render_metric_card(
        "Final Score",
        f"{result.scores.final_score}/100",
        metric_color_by_score(result.scores.final_score),
        "Overall weighted evaluation",
    )

with summary_cols[2]:
    render_metric_card(
        "Win Probability",
        f"{win_probability}%",
        "#7c3aed",
        "Likelihood of winning if you apply",
    )

with summary_cols[3]:
    render_metric_card(
        "Confidence",
        confidence_label,
        confidence_color(confidence_label),
        "How complete and reliable the signal set is",
    )


# ============================================================
# TABS
# ============================================================

tab_decision, tab_strategy, tab_proposal, tab_debug = st.tabs(
    ["Decision", "Strategy", "Proposal", "Debug"]
)


# ============================================================
# TAB 1: DECISION
# ============================================================

with tab_decision:
    left, right = st.columns(2)

    with left:
        st.markdown('<div class="section-title">Core Opportunity Signals</div>', unsafe_allow_html=True)
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        render_score_block("Technical Fit", result.scores.technical_fit, "Can you do this well?")
        render_score_block("Client Quality", result.scores.client_quality, "Is the client serious and reliable?")
        render_score_block("Value", result.scores.value, "Is this opportunity worth the effort?")
        render_score_block("Timing", result.scores.timing, "Are you early enough in the process?")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-title">Risk & Confidence Signals</div>', unsafe_allow_html=True)
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        render_score_block("Competition Risk", result.scores.competition_risk, "Higher = harder to win")
        render_score_block("Clarity", result.scores.clarity, "How clearly the job is defined")
        render_score_block("Execution Risk", result.scores.execution_risk, "Higher = more technical uncertainty")
        render_score_block("Confidence", result.scores.confidence, "How complete the available data is")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Why This Decision</div>', unsafe_allow_html=True)

    r1, r2 = st.columns(2)

    with r1:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        render_reason_list("Reasons", result.reasons, "No reasons generated.")
        st.markdown("</div>", unsafe_allow_html=True)

    with r2:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        render_reason_list("Risks", result.risks, "No risks generated.")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("How to read these metrics"):
        st.markdown(
            """
**Technical Fit** — how well your skills match the job.

**Client Quality** — how reliable and serious the client appears.

**Value** — whether the opportunity is worth your effort overall.

**Timing** — how early or late you are in the hiring process.

**Competition Risk** — how crowded and difficult the opportunity is.

**Clarity** — how well the job is defined.

**Execution Risk** — how much delivery uncertainty the project may have.
"""
        )


# ============================================================
# TAB 2: STRATEGY
# ============================================================

with tab_strategy:
    st.markdown(
        f"""
        <div class="soft-card" style="margin-bottom:16px;">
            <div style="font-size:14px; color:#6b7280; margin-bottom:8px;">Recommended play</div>
            <div style="font-size:20px; font-weight:800; color:#111827;">
                {result.action.proposal_mode} proposal, {'boost' if result.action.should_boost else 'no boost'}, {'auto-apply allowed' if result.action.auto_apply else 'manual review'}.
            </div>
            <div style="font-size:14px; color:#6b7280; margin-top:8px;">
                Pricing mode: {result.action.pricing_mode}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    s1, s2, s3, s4 = st.columns(4)

    with s1:
        render_metric_card(
            "Proposal Mode",
            result.action.proposal_mode,
            "#111827",
            "How much effort to invest in the proposal",
        )

    with s2:
        render_metric_card(
            "Auto Apply",
            "YES" if result.action.auto_apply else "NO",
            "#15803d" if result.action.auto_apply else "#b91c1c",
            "Can this be applied automatically?",
        )

    with s3:
        render_metric_card(
            "Boost",
            "YES" if result.action.should_boost else "NO",
            "#7c3aed" if result.action.should_boost else "#111827",
            "Is it worth paying extra for visibility?",
        )

    with s4:
        render_metric_card(
            "Pricing Mode",
            result.action.pricing_mode,
            "#111827",
            "How aggressively to position pricing",
        )

    st.markdown('<div class="section-title">Suggested Bid Range</div>', unsafe_allow_html=True)

    b1, b2, b3 = st.columns(3)

    with b1:
        render_metric_card("Bid Low", format_currency(result.action.bid_low))

    with b2:
        render_metric_card("Bid Mid", format_currency(result.action.bid_mid))

    with b3:
        render_metric_card("Bid High", format_currency(result.action.bid_high))

    st.markdown('<div class="section-title">Strategy Notes</div>', unsafe_allow_html=True)
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)

    strategy_notes = []

    if result.action.proposal_mode == "PREMIUM":
        strategy_notes.append("Use a more tailored proposal with stronger positioning and clearer delivery structure.")
    elif result.action.proposal_mode == "STANDARD":
        strategy_notes.append("A standard tailored proposal is enough for this opportunity.")
    else:
        strategy_notes.append("Do not spend time writing a full proposal for this opportunity.")

    if result.action.should_boost:
        strategy_notes.append("Boost is justified because the opportunity looks strong enough to pay for extra visibility.")
    else:
        strategy_notes.append("Boost is not justified here; keep connect spend conservative.")

    if result.action.auto_apply:
        strategy_notes.append("This job is clean enough for automated submission rules.")
    else:
        strategy_notes.append("Manual review is safer before applying.")

    if result.action.pricing_mode == "aggressive":
        strategy_notes.append("The opportunity supports confident pricing near the upper end.")
    elif result.action.pricing_mode == "conservative":
        strategy_notes.append("Keep pricing careful due to weak value, clarity, or client signals.")
    elif result.action.pricing_mode == "balanced":
        strategy_notes.append("Use balanced pricing around the middle of the available budget.")

    for note in strategy_notes:
        st.markdown(f"- {note}")

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# TAB 3: PROPOSAL
# ============================================================

with tab_proposal:
    st.markdown(
        """
        <div class="soft-card" style="margin-bottom:16px;">
            <div style="font-size:14px; color:#6b7280; margin-bottom:8px;">Proposal workspace</div>
            <div style="font-size:20px; font-weight:800; color:#111827;">
                Review the selected proposal, compare versions, and download the final text.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    proposal_tab1, proposal_tab2, proposal_tab3 = st.tabs(["Selected", "Standard", "Premium"])

    with proposal_tab1:
        st.text_area(
            "Proposal to use",
            proposal.full_proposal,
            height=520,
            key="selected_proposal",
        )
        st.download_button(
            "Download selected proposal",
            data=proposal.full_proposal,
            file_name=proposal_filename(proposal.title, "selected"),
            mime="text/plain",
            use_container_width=True,
        )

    with proposal_tab2:
        st.text_area(
            "Standard proposal",
            proposal.standard_full_proposal,
            height=520,
            key="standard_proposal",
        )
        st.download_button(
            "Download standard proposal",
            data=proposal.standard_full_proposal,
            file_name=proposal_filename(proposal.title, "standard"),
            mime="text/plain",
            use_container_width=True,
        )

    with proposal_tab3:
        st.text_area(
            "Premium proposal",
            proposal.premium_full_proposal,
            height=520,
            key="premium_proposal",
        )
        st.download_button(
            "Download premium proposal",
            data=proposal.premium_full_proposal,
            file_name=proposal_filename(proposal.title, "premium"),
            mime="text/plain",
            use_container_width=True,
        )

    with st.expander("Proposal sections"):
        st.text_area(
            "Cover letter",
            proposal.cover_letter,
            height=220,
            key="cover_letter_section",
        )
        st.text_area(
            "Relevant experience",
            proposal.relevant_experience,
            height=220,
            key="relevant_experience_section",
        )
        st.text_area(
            "Approach",
            proposal.approach,
            height=260,
            key="approach_section",
        )


# ============================================================
# TAB 4: DEBUG
# ============================================================

with tab_debug:
    st.subheader("Debug / Raw Output")

    with st.expander("Structured result", expanded=True):
        st.json(
            {
                "decision": result.decision,
                "confidence_label": confidence_label,
                "win_probability": win_probability,
                "scores": {
                    "technical_fit": result.scores.technical_fit,
                    "client_quality": result.scores.client_quality,
                    "competition_risk": result.scores.competition_risk,
                    "value": result.scores.value,
                    "timing": result.scores.timing,
                    "clarity": result.scores.clarity,
                    "execution_risk": result.scores.execution_risk,
                    "confidence": result.scores.confidence,
                    "final_score": result.scores.final_score,
                },
                "action": {
                    "proposal_mode": result.action.proposal_mode,
                    "should_boost": result.action.should_boost,
                    "auto_apply": result.action.auto_apply,
                    "pricing_mode": result.action.pricing_mode,
                    "bid_low": result.action.bid_low,
                    "bid_mid": result.action.bid_mid,
                    "bid_high": result.action.bid_high,
                },
                "inputs": {
                    "title": title,
                    "category": category,
                    "proposal_band": proposal_band,
                    "client_hire_rate": client_hire_rate,
                    "skills_list": skills_list,
                },
                "proposal_preview": {
                    "selected_mode": proposal_mode,
                    "title": proposal.title,
                },
                "reasons": result.reasons,
                "risks": result.risks,
            }
        )

    with st.expander("Current derived notes"):
        st.markdown(f"- Proposal bucket: **{proposal_band}**")
        st.markdown(f"- Derived skills: **{', '.join(skills_list) if skills_list else '—'}**")
        st.markdown(f"- Selected proposal mode: **{proposal_mode}**")
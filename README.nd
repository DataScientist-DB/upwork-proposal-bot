Upwork Proposal Bot

A decision-support and proposal-generation tool for evaluating Upwork jobs and writing high-quality, tailored proposals.

This app helps answer three critical questions:

Should I apply to this job?
Why or why not?
What proposal should I send?
🚀 Live Demo

👉 (Add your Streamlit link here after deployment)
Example: https://your-app-name.streamlit.app

✨ Features
🔍 Smart Job Evaluation
Technical fit detection from job description
Client quality scoring (hire rate, spend, reviews, activity)
Competition and timing analysis
Value assessment (effort vs opportunity)
📊 Decision & Probability Engine
Clear decisions: SKIP, APPLY, STRONG_APPLY
Win probability estimation
Confidence level based on data completeness
🧠 Strategy Engine
Proposal mode: NONE, STANDARD, PREMIUM
Boost recommendation (when to spend connects)
Auto-apply logic
Pricing strategy:
Conservative
Balanced
Aggressive
Suggested bid range
✍️ Proposal Generator
Generates Standard and Premium proposals
Clean structure:
Cover letter
Relevant experience
Approach
Non-repetitive content
Copy-ready + downloadable
🖥️ SaaS-Style Dashboard (Streamlit)
Interactive UI
Visual score breakdown
Strategy insights
Proposal workspace (tabs + download)
Debug panel for transparency
📸 Screenshots
🔍 Decision Dashboard




🧠 Strategy Recommendations




✍️ Proposal Generator




🧾 Job Input Panel




🎥 Demo




🏗️ Project Structure
upwork_proposal_bot/
│
├── app/
│   ├── main.py                # CLI entry point
│   ├── streamlit_app.py      # Streamlit UI (main app)
│   ├── engine.py             # Orchestration layer
│   ├── scoring.py            # Scoring logic
│   ├── decision.py           # Decision logic
│   ├── strategy.py           # Strategy engine
│   ├── proposal_writer.py    # Proposal generation
│   ├── parser.py             # Job parsing
│   ├── explain.py            # Reasons & risks
│   └── models.py             # Data models
│
├── assets/                   # Screenshots / demo GIF
├── requirements.txt
└── README.md
▶️ Run Locally
1. Clone repository
git clone https://github.com/YOUR_USERNAME/upwork_proposal_bot.git
cd upwork_proposal_bot
2. Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Mac/Linux
3. Install dependencies
pip install -r requirements.txt
4. Run app
python -m streamlit run app/streamlit_app.py

Open:

http://localhost:8501
🧪 Run Backend (CLI)
python -m app.main

Outputs:

Decision
Score
Win Probability
Confidence
Strategy
Reasons & Risks
☁️ Deployment (Streamlit Cloud)
Push project to GitHub
Go to https://streamlit.io/cloud
Click New App
Select:
Repository
Branch: main
Entry file: app/streamlit_app.py
Deploy 🚀
🧠 Methodology
Core Metrics
Metric	Meaning
Technical Fit	Can you do the job well?
Client Quality	Is the client reliable?
Timing	Are you early enough?
Competition Risk	How crowded is the job?
Value	Is it worth your effort?
Clarity	How well defined is the job?
Execution Risk	Delivery uncertainty
Decision Logic
SKIP → Not worth time
APPLY → Decent opportunity
STRONG_APPLY → High-value job
Strategy Logic
Proposal Mode
NONE → skip
STANDARD → normal effort
PREMIUM → high-effort tailored proposal
Boost
Only when high probability + strong value + good client
Pricing
Conservative / Balanced / Aggressive
✍️ Proposal Design Philosophy

Each proposal follows:

Clear understanding of the problem
Credibility positioning
Relevant experience (no repetition)
Structured approach
Deliverables + clarifications
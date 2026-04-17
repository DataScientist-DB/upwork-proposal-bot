from app.models import JobInput
from app.engine import evaluate_job

job = JobInput(
    title="Web scraper needed",
    description="Extract product data including prices, descriptions, images from website.",
    category="scraping",
    payment_verified=True,
    proposals_count=10,
    interviewing_count=0,
    invites_sent=0,
    unanswered_invites=0,
    last_viewed_hours_ago=1,
    client_hire_rate=40,
    client_total_spent=2000,
    budget_min=400,
    budget_max=1000,
)

print("RUNNING EVALUATION ONCE")

result = evaluate_job(job)

# extract probability from reasons TEMPORARILY if needed
# (quick hack if not yet in model)
for r in result.reasons:
    if "Estimated probability" in r:
        win_probability = r.split(":")[1].strip().replace("%", "")

print("=== RESULT ===")
print("Decision:", result.decision)
print("Score:", result.scores.final_score)
print("Win Probability:", f"{result.win_probability}%")
print("Confidence:", result.confidence_label)
print("Proposal Mode:", result.action.proposal_mode)
print("Auto Apply:", result.action.auto_apply)

print("\nReasons:")
for r in result.reasons:
    print("-", r)

print("\nRisks:")
for r in result.risks:
    print("-", r)
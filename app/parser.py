from __future__ import annotations

import re
from app.models import JobInput, ParsedSignals


def _contains_any(text: str, phrases: list[str]) -> bool:
    text = text.lower()
    return any(p.lower() in text for p in phrases)


def parse_job(job: JobInput) -> ParsedSignals:
    text = f"{job.title}\n{job.description}".lower()

    s = ParsedSignals()

    s.mentions_scraping = _contains_any(text, ["scrap", "crawler", "crawl", "extract data", "web scraper"])
    s.mentions_automation = _contains_any(text, ["automation", "pipeline", "automated"])
    s.mentions_apify = _contains_any(text, ["apify"])
    s.mentions_large_dataset = _contains_any(text, ["large datasets", "large dataset", "high volume", "scale"])
    s.mentions_images = _contains_any(text, ["images", "photos", "image urls"])
    s.mentions_csv = _contains_any(text, ["csv"])
    s.mentions_excel = _contains_any(text, ["excel", "xlsx"])
    s.mentions_json = _contains_any(text, ["json"])
    s.mentions_api = _contains_any(text, ["api"])
    s.mentions_anti_bot = _contains_any(text, ["captcha", "anti-bot", "cloudflare", "rate limit"])
    s.mentions_browser_automation = _contains_any(text, ["selenium", "playwright", "browser automation"])

    s.mentions_target_website = bool(re.search(r"https?://|website|site", text))
    s.mentions_output_format = s.mentions_csv or s.mentions_excel or s.mentions_json or _contains_any(
        text, ["structured format", "structured data"]
    )
    s.mentions_deliverables = _contains_any(text, ["deliverables", "output", "provide", "export"])
    s.mentions_scale = s.mentions_large_dataset or _contains_any(text, ["thousands", "millions", "bulk"])

    # clarity
    clarity = 0
    if s.mentions_target_website:
        clarity += 25
    if s.mentions_output_format:
        clarity += 20
    if s.mentions_deliverables:
        clarity += 15
    if job.budget_min or job.budget_max or job.hourly_min or job.hourly_max:
        clarity += 15
    if len(job.description.strip()) >= 250:
        clarity += 10
    if _contains_any(text, ["timeline", "deadline", "ongoing", "weekly"]):
        clarity += 10
    if _contains_any(text, ["specific website", "details will be shared", "more info later"]):
        clarity -= 10
    s.clarity_score = max(0, min(100, clarity))

    # execution risk
    risk = 20
    if s.mentions_large_dataset:
        risk += 15
    if not s.mentions_target_website:
        risk += 15
    if _contains_any(text, ["dynamic", "javascript rendered", "login", "protected"]):
        risk += 20
    if s.mentions_anti_bot:
        risk += 20
    if _contains_any(text, ["real-time", "daily sync", "ongoing updates"]):
        risk += 10
    s.execution_risk_score = max(0, min(100, risk))

    # technical fit
    fit = 20
    if s.mentions_scraping:
        fit += 30
    if s.mentions_automation:
        fit += 10
    if s.mentions_large_dataset:
        fit += 10
    if s.mentions_output_format:
        fit += 10
    if s.mentions_images:
        fit += 5
    if s.mentions_api or s.mentions_browser_automation:
        fit += 5
    if "scraping" in job.category.lower():
        fit += 10
    s.technical_fit_score = max(0, min(100, fit))

    # category fit
    category_fit = 30
    if "scrap" in job.category.lower():
        category_fit += 35
    if s.mentions_scraping:
        category_fit += 20
    s.category_fit_score = max(0, min(100, category_fit))

    return s
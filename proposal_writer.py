from __future__ import annotations

from typing import Dict, List


class ProposalWriter:
    # -------------------------------------------------
    # Core matching / signal extraction
    # -------------------------------------------------

    def build_proof_block(self, job_text: str, past_projects: List[dict], max_items: int = 3) -> str:
        text = (job_text or "").lower()
        matches = []

        for project in past_projects:
            for tag in project.get("tags", []):
                if tag.lower() in text:
                    matches.append(project["summary"])
                    break

        if not matches:
            matches = [project["summary"] for project in past_projects[:max_items]]

        return "\n".join(f"- {item}" for item in matches[:max_items]).strip()

    def extract_signals(self, text: str) -> dict:
        text = (text or "").lower()

        return {
            "cloudflare": any(k in text for k in ["cloudflare", "bot detection", "anti-bot", "captcha"]),
            "scale_pages": any(k in text for k in ["5000 pages", "5,000 pages", "thousands of pages"]),
            "many_scrapers": any(k in text for k in ["50-100 scrapers", "50–100 scrapers", "multiple scrapers"]),
            "third_party_tool": any(k in text for k in ["third party software", "commercial-grade"]),
            "scraping": any(k in text for k in ["scrape", "scraping", "extract html", "crawler", "crawl"]),
            "streamlit": any(k in text for k in ["streamlit", "dashboard"]),
            "pdf": any(k in text for k in ["pdf", "report", "reporting", "document generation"]),
            "pipeline": any(
                k in text
                for k in [
                    "pipeline",
                    "etl",
                    "json",
                    "csv",
                    "xlsx",
                    "cleaning",
                    "parsing",
                    "reconciliation",
                    "cogs",
                    "inventory sync",
                    "audit trail",
                ]
            ),
            "api": "api" in text,
            "automation": any(k in text for k in ["automation", "workflow", "script", "bot", "sync"]),
            "lead_gen": any(k in text for k in ["lead", "prospect", "contact extraction", "company data"]),
            "sql": any(k in text for k in ["sql", "postgresql", "supabase"]),
            "shopify": "shopify" in text,
            "inventory": any(k in text for k in ["inventory", "stock levels", "warehouse", "in-stock"]),
            "validation": any(k in text for k in ["validation", "validate", "audit trail", "traceable"]),
            "direct_question": self._has_direct_question(text),
            "strict_accuracy": any(
                k in text
                for k in [
                    "verify your own work",
                    "wrong numbers that look right are worse than no numbers",
                    "real numbers, not estimates",
                    "traceable to its source",
                ]
            ),
        }

    # -------------------------------------------------
    # Intent detection
    # -------------------------------------------------

    def _has_direct_question(self, text: str) -> bool:
        triggers = [
            "tell me about a time",
            "describe a time",
            "give an example",
            "how did you prove",
            "how you proved",
            "what did you do when",
        ]
        return any(t in text for t in triggers)

    def _needs_story_mode(self, text: str, signals: dict) -> bool:
        if signals.get("direct_question"):
            return True

        story_phrases = [
            "everyone else missed",
            "how you proved it was wrong",
            "found a data error",
            "prove it was wrong",
        ]
        return any(p in text for p in story_phrases)

    # -------------------------------------------------
    # Inference blocks
    # -------------------------------------------------

    def infer_immediate_need(self, text: str, s: dict) -> str:
        if s["sql"] and s["inventory"] and s["validation"]:
            return "build a trustworthy reconciliation and sync layer where inventory, cost, and source-of-truth data stay aligned"
        if s["cloudflare"] and s["scraping"]:
            return "extract the required data reliably from a protected source without turning the workflow into a fragile one-off build"
        if s["scraping"] and s["many_scrapers"]:
            return "set up a repeatable extraction workflow that can be reused across multiple sources"
        if s["pipeline"] and s["pdf"]:
            return "turn raw input into structured outputs that are usable in reporting and downstream workflows"
        if s["pipeline"]:
            return "clean, structure, and standardize incoming data so it becomes operationally usable"
        if s["streamlit"]:
            return "turn the underlying data/process into a usable working interface"
        if s["automation"]:
            return "replace manual effort with a repeatable workflow that behaves predictably"
        return "solve the immediate requirement in a way that remains usable after delivery"

    def infer_underlying_problem(self, text: str, s: dict) -> str:
        if s["sql"] and s["inventory"] and s["validation"]:
            return "the difficulty is not moving numbers between systems, but proving that each number remains reconcilable, traceable, and trustworthy end to end"
        if s["cloudflare"] and s["many_scrapers"]:
            return "the real challenge is not the first extraction run, but creating a collection layer that can survive protection mechanisms and still scale across future targets"
        if s["cloudflare"]:
            return "the real challenge is not only access, but maintaining consistent collection when the source is actively resisting automation"
        if s["scraping"] and s["scale_pages"]:
            return "the real challenge is not volume alone, but how to keep the extraction logic maintainable as the dataset grows"
        if s["pipeline"] and s["pdf"]:
            return "the real challenge is not producing a report once, but ensuring the pipeline can keep generating consistent outputs as inputs evolve"
        if s["streamlit"]:
            return "the real challenge is not only displaying information, but turning a process into something people can actually use and act on"
        if s["pipeline"]:
            return "the real challenge is not collecting data, but shaping it into a form that remains reliable across downstream use cases"
        return "the real challenge is usually not the first delivery, but whether the solution continues to work cleanly as the use case expands"

    def infer_expansion_opportunities(self, text: str, s: dict) -> List[str]:
        opportunities: List[str] = []

        if s["sql"] and s["inventory"]:
            opportunities.append("a stronger source-of-truth model for inventory and cost movement across systems")
            opportunities.append("exception surfacing so mismatches are visible immediately instead of hiding inside seemingly correct totals")

        if s["scraping"]:
            opportunities.append("a reusable extraction pattern so future sources can be added faster")
            opportunities.append("normalized outputs so the collected data stays comparable across runs or sources")

        if s["cloudflare"]:
            opportunities.append("a cleaner separation between access strategy, parsing logic, and downstream processing")

        if s["many_scrapers"]:
            opportunities.append("a framework for onboarding additional scrapers without rebuilding the whole workflow each time")

        if s["pipeline"]:
            opportunities.append("validation and transformation steps that make the data more useful for analytics, reporting, or operational use")
            opportunities.append("structured exports that support later integration into dashboards, internal tools, or other systems")

        if s["streamlit"]:
            opportunities.append("an interface layer that can later become an internal decision tool rather than just a view of raw output")

        if s["pdf"]:
            opportunities.append("repeatable document/report generation from the same structured data foundation")

        if s["lead_gen"]:
            opportunities.append("a path from raw extraction to enrichment, qualification, and CRM-ready outputs")

        deduped = []
        seen = set()
        for item in opportunities:
            if item not in seen:
                deduped.append(item)
                seen.add(item)

        return deduped[:3]

    def infer_methodology(self, text: str, s: dict) -> List[str]:
        steps: List[str] = []

        if s["sql"] and s["inventory"] and s["validation"]:
            steps.append("define the reconciliation logic around source-of-truth rules first, so mismatches can be explained rather than just observed")
            steps.append("validate each stage against upstream source data instead of trusting transformed outputs by default")
            steps.append("surface failed joins, missing mappings, and broken assumptions explicitly so errors cannot hide inside clean-looking totals")

        if s["cloudflare"]:
            steps.append("separate source access strategy from extraction logic so protection issues do not contaminate the whole workflow")

        if s["scraping"]:
            steps.append("stabilize the extraction pattern on representative pages first, then extend it across the wider source set")
            steps.append("shape the output schema early so collection stays aligned with downstream use")

        if s["pipeline"]:
            steps.append("introduce cleaning, normalization, and validation close to ingestion rather than leaving quality issues until the end")

        if s["streamlit"]:
            steps.append("treat the interface as the operational layer of the workflow, not as a separate afterthought")

        if s["pdf"]:
            steps.append("keep reporting outputs tied to structured source data so regeneration stays consistent")

        if not steps:
            steps.append("define the working structure early so the solution remains extensible rather than task-bound")

        deduped = []
        seen = set()
        for step in steps:
            if step not in seen:
                deduped.append(step)
                seen.add(step)

        return deduped[:3]

    def infer_relevant_experience_lines(self, text: str, s: dict, past_projects: List[dict]) -> List[str]:
        lines: List[str] = []

        tag_priority = []
        if s["sql"] or s["inventory"] or s["validation"]:
            tag_priority.extend(["data pipeline", "etl", "csv", "json", "xlsx", "automation"])
        if s["cloudflare"] or s["scraping"]:
            tag_priority.extend(["apify", "web scraping", "automation", "playwright", "beautifulsoup"])
        if s["streamlit"]:
            tag_priority.extend(["streamlit", "dashboard", "analytics"])
        if s["pdf"]:
            tag_priority.extend(["pdf", "document", "reporting", "automation"])

        for preferred_tag in tag_priority:
            for project in past_projects:
                tags = [t.lower() for t in project.get("tags", [])]
                if preferred_tag in tags:
                    summary = project["summary"]
                    if summary not in lines:
                        lines.append(summary)

        if not lines:
            lines = [project["summary"] for project in past_projects[:3]]

        return lines[:3]

    # -------------------------------------------------
    # Openings / body builders
    # -------------------------------------------------

    def build_standard_opening(self, immediate_need: str) -> str:
        return f"Hi,\n\nI read this as a need to {immediate_need}."

    def build_premium_opening(self, underlying_problem: str) -> str:
        return f"Hi,\n\nThe core issue here is that {underlying_problem}."

    def build_standard_body(
        self,
        methodology: List[str],
        experience_lines: List[str],
        opportunities: List[str],
        name: str,
    ) -> str:
        method_text = ""
        if methodology:
            method_text = "A practical way to handle this is to:\n" + "\n".join(f"- {step}" for step in methodology) + "\n\n"

        experience_text = ""
        if experience_lines:
            experience_text = "Related work on my side includes:\n" + "\n".join(f"- {line}" for line in experience_lines) + "\n\n"

        opportunity_text = ""
        if opportunities:
            opportunity_text = (
                "Handled this way, the same work can also support:\n"
                + "\n".join(f"- {item}" for item in opportunities[:2])
                + "\n\n"
            )

        closing = (
            "So the result is not only a delivered task, but a workflow that is easier to extend and reuse after the first phase.\n\n"
            f"Best,\n{name}"
        )

        return method_text + experience_text + opportunity_text + closing

    def build_premium_body(
        self,
        immediate_need: str,
        methodology: List[str],
        experience_lines: List[str],
        opportunities: List[str],
        name: str,
    ) -> str:
        reframing = (
            f"What matters is not only how to {immediate_need}, "
            "but how to do it in a way that creates a stable foundation for whatever comes next.\n\n"
        )

        method_text = ""
        if methodology:
            method_text = (
                "My preference in projects like this is to structure the work so the first delivery also improves the next phase:\n"
                + "\n".join(f"- {step}" for step in methodology)
                + "\n\n"
            )

        experience_text = ""
        if experience_lines:
            experience_text = (
                "That perspective comes from work built around:\n"
                + "\n".join(f"- {line}" for line in experience_lines)
                + "\n\n"
            )

        opportunity_text = ""
        if opportunities:
            opportunity_text = (
                "Approached this way, the immediate solution can also open up:\n"
                + "\n".join(f"- {item}" for item in opportunities)
                + "\n\n"
            )

        control_text = (
            "I would keep the delivery grounded: prove the approach on the current requirement first, then shape it so it can be extended cleanly without carrying unnecessary complexity into phase one.\n\n"
        )

        closing = (
            "That usually leads to a better result for the client: the initial problem gets solved, but the work also becomes more reusable, more informative, and more valuable over time.\n\n"
            f"Best,\n{name}"
        )

        return reframing + method_text + experience_text + opportunity_text + control_text + closing

    # -------------------------------------------------
    # Story mode for direct client questions
    # -------------------------------------------------

    def build_story_answer_short(self, name: str) -> str:
        return (
            "Hi,\n\n"
            "This reads less like a basic pipeline task and more like a data integrity problem across systems.\n\n"
            "One similar case I worked on involved inventory, sales, and warehouse numbers that all looked correct in isolation but failed when reconciled end-to-end. I traced it back by validating each stage against source events rather than trusting derived tables, which exposed where the numbers diverged.\n\n"
            "That is generally how I approach this kind of work: make mismatches visible and provable, not just corrected at the final output.\n\n"
            f"Best,\n{name}"
        )

    def build_story_answer_standard(self, name: str) -> str:
        return (
            "Hi,\n\n"
            "One example that is very similar:\n\n"
            "I worked on a system where inventory, sales, and warehouse data were all internally consistent, but did not reconcile end-to-end.\n\n"
            "The issue turned out to be subtle:\n"
            "- fulfillment updates lagged behind reporting snapshots\n"
            "- cost logic was being applied on partially updated inventory states\n"
            "- each system looked correct in isolation, but failed when traced across the full flow\n\n"
            "I proved it by reconstructing the pipeline from source events to transformations to outputs, and validating each stage against its original source instead of trusting derived tables.\n\n"
            "That exposed exactly where the numbers diverged.\n\n"
            "Fixing it was less about rewriting queries and more about restructuring validation so mismatches could not pass silently.\n\n"
            "That is generally how I approach systems like this: first make the numbers explainable, then make the pipeline durable.\n\n"
            f"Best,\n{name}"
        )

    def build_story_answer_premium(self, name: str) -> str:
        return (
            "Hi,\n\n"
            "A closely related example:\n\n"
            "I worked on a data flow where inventory, sales, and warehouse states all appeared correct inside their own systems, yet the business-level numbers still failed to reconcile.\n\n"
            "The underlying problem was not a visible query error. It was timing and transformation drift:\n"
            "- fulfillment updates were arriving on a different cadence than reporting snapshots\n"
            "- cost calculations were being applied to partially updated inventory states\n"
            "- the outputs looked plausible, which made the error harder to catch\n\n"
            "I proved it by rebuilding the full chain from source events to transformed tables to final outputs, and comparing each stage back to its original source instead of assuming the derived layer was trustworthy.\n\n"
            "That made it possible to show exactly where the divergence started, rather than only where the final totals looked wrong.\n\n"
            "The fix was not just a query adjustment. It required changing the validation structure so mismatches became visible immediately and could no longer pass as believable numbers.\n\n"
            "That is the kind of discipline I would bring here as well: not only getting the pipeline to run, but making every important number defensible and traceable.\n\n"
            f"Best,\n{name}"
        )

    # -------------------------------------------------
    # Public writers
    # -------------------------------------------------

    def write_short(self, profile: dict, job_text: str, past_projects: List[dict]) -> str:
        text = (job_text or "").lower()
        signals = self.extract_signals(text)
        name = profile.get("name", "")

        if self._needs_story_mode(text, signals):
            return self.build_story_answer_short(name)

        if signals["sql"] and signals["inventory"] and signals["validation"]:
            return (
                "Hi,\n\n"
                "This reads less like a basic pipeline task and more like a data integrity problem across systems.\n\n"
                "I would handle it by reconciling each movement against source-of-truth rules, surfacing failed mappings and mismatches explicitly, and making sure the outputs stay traceable rather than merely plausible.\n\n"
                f"Best,\n{name}"
            )

        if signals["cloudflare"] and signals["scraping"]:
            return (
                "Hi,\n\n"
                "This is the kind of scraping problem where the real value is in making the setup reusable, not just getting one successful extraction.\n\n"
                "I would approach it so the current target works reliably, but the same structure can support later scraper onboarding without rebuilding everything from scratch.\n\n"
                f"Best,\n{name}"
            )

        if signals["pipeline"]:
            return (
                "Hi,\n\n"
                "This looks less like a one-off script and more like a workflow that needs clean structure from ingestion through output.\n\n"
                "I would focus on keeping the data validated, normalized, and usable downstream so the result supports more than the immediate task.\n\n"
                f"Best,\n{name}"
            )

        return (
            "Hi,\n\n"
            "I would approach this by solving the immediate requirement in a way that remains stable and reusable after the first delivery.\n\n"
            "That usually means shaping the structure early, validating the important assumptions, and avoiding a solution that only works for the first case.\n\n"
            f"Best,\n{name}"
        )

    def write_standard(self, profile: dict, job_text: str, past_projects: List[dict]) -> str:
        text = (job_text or "").lower()
        signals = self.extract_signals(text)
        name = profile.get("name", "")

        if self._needs_story_mode(text, signals):
            return self.build_story_answer_standard(name)

        immediate_need = self.infer_immediate_need(text, signals)
        methodology = self.infer_methodology(text, signals)
        opportunities = self.infer_expansion_opportunities(text, signals)
        experience_lines = self.infer_relevant_experience_lines(text, signals, past_projects)

        opening = self.build_standard_opening(immediate_need)
        body = self.build_standard_body(
            methodology=methodology,
            experience_lines=experience_lines,
            opportunities=opportunities,
            name=name,
        )

        return opening + "\n\n" + body

    def write_premium(self, profile: dict, job_text: str, past_projects: List[dict]) -> str:
        text = (job_text or "").lower()
        signals = self.extract_signals(text)
        name = profile.get("name", "")

        if self._needs_story_mode(text, signals):
            return self.build_story_answer_premium(name)

        immediate_need = self.infer_immediate_need(text, signals)
        underlying_problem = self.infer_underlying_problem(text, signals)
        methodology = self.infer_methodology(text, signals)
        opportunities = self.infer_expansion_opportunities(text, signals)
        experience_lines = self.infer_relevant_experience_lines(text, signals, past_projects)

        opening = self.build_premium_opening(underlying_problem)
        body = self.build_premium_body(
            immediate_need=immediate_need,
            methodology=methodology,
            experience_lines=experience_lines,
            opportunities=opportunities,
            name=name,
        )

        return opening + "\n\n" + body

    def write_selected(
        self,
        profile: dict,
        job_text: str,
        past_projects: List[dict],
        mode: str = "standard",
    ) -> str:
        mode_normalized = (mode or "standard").strip().lower()

        if mode_normalized == "skip":
            return "Low-fit job based on current scoring signals. Recommended action: skip."

        if mode_normalized == "short":
            return self.write_short(profile, job_text, past_projects)

        if mode_normalized == "premium":
            return self.write_premium(profile, job_text, past_projects)

        return self.write_standard(profile, job_text, past_projects)
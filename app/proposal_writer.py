from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ProposalOutput:
    title: str
    cover_letter: str
    relevant_experience: str
    approach: str
    full_proposal: str
    premium_full_proposal: str
    standard_full_proposal: str


class ProposalWriter:
    """
    Single proposal-writing module for the Upwork Proposal Bot.

    Notes:
    - Keeps proposal generation in one place
    - Works with either dicts or model-like objects
    - Does not require changes to models.py
    - Supports Streamlit integration via generate_from_fields(...)
    """

    PLATFORM_EXPERIENCE_PARAGRAPH = (
        "I am relatively new to the Upwork platform, so most of my experience comes from work completed outside of Upwork. "
        "I have projects published on Apify, and I can also share relevant work published through Upwork-compatible demos and Streamlit-based tools when useful. "
        "I can provide relevant examples of projects developed outside of Upwork upon request through Upwork."
    )

    def generate(self, job: Any, evaluation: Any) -> ProposalOutput:
        job_data = self._extract_job_data(job)
        eval_data = self._extract_evaluation_data(evaluation)

        title = job_data["title"]
        description = job_data["description"]
        skills = job_data["skills"]

        proposal_mode = eval_data["proposal_mode"]
        score = eval_data["score"]
        win_probability = eval_data["win_probability"]
        confidence = eval_data["confidence"]
        reasons = eval_data["reasons"]
        risks = eval_data["risks"]

        keywords = self._build_keyword_blob(title, description, skills)
        strengths = self._select_relevant_strengths(keywords)
        focus_points = self._select_focus_points(keywords)
        deliverables = self._select_deliverables(keywords)

        standard_cover = self._build_cover_letter(
            title=title,
            strengths=strengths,
            focus_points=focus_points,
            score=score,
            win_probability=win_probability,
            confidence=confidence,
            mode="STANDARD",
        )
        standard_experience = self._build_relevant_experience(
            strengths=strengths,
            keywords=keywords,
            premium=False,
        )
        standard_approach = self._build_approach(
            focus_points=focus_points,
            deliverables=deliverables,
            risks=risks,
            mode="STANDARD",
        )
        standard_full = self._join_sections(
            standard_cover,
            standard_experience,
            standard_approach,
        )

        premium_cover = self._build_cover_letter(
            title=title,
            strengths=strengths,
            focus_points=focus_points,
            score=score,
            win_probability=win_probability,
            confidence=confidence,
            mode="PREMIUM",
        )
        premium_experience = self._build_relevant_experience(
            strengths=strengths,
            keywords=keywords,
            premium=True,
        )
        premium_approach = self._build_approach(
            focus_points=focus_points,
            deliverables=deliverables,
            risks=risks,
            mode="PREMIUM",
        )
        premium_full = self._join_sections(
            premium_cover,
            premium_experience,
            premium_approach,
        )

        if proposal_mode.upper() == "PREMIUM":
            selected_cover = premium_cover
            selected_experience = premium_experience
            selected_approach = premium_approach
            selected_full = premium_full
        else:
            selected_cover = standard_cover
            selected_experience = standard_experience
            selected_approach = standard_approach
            selected_full = standard_full

        if reasons and any("clarifying requirements" in str(r).lower() for r in reasons):
            selected_full = self._soften_scope_claims(selected_full)

        return ProposalOutput(
            title=title,
            cover_letter=selected_cover,
            relevant_experience=selected_experience,
            approach=selected_approach,
            full_proposal=selected_full,
            premium_full_proposal=premium_full,
            standard_full_proposal=standard_full,
        )

    def generate_from_fields(
        self,
        title: str,
        description: str,
        skills: Optional[List[str]] = None,
        score: int = 0,
        win_probability: int = 0,
        confidence: str = "MEDIUM",
        proposal_mode: str = "STANDARD",
        reasons: Optional[List[str]] = None,
        risks: Optional[List[str]] = None,
    ) -> ProposalOutput:
        job = {
            "title": title,
            "description": description,
            "skills": skills or [],
        }
        evaluation = {
            "score": score,
            "win_probability": win_probability,
            "confidence": confidence,
            "proposal_mode": proposal_mode,
            "reasons": reasons or [],
            "risks": risks or [],
        }
        return self.generate(job=job, evaluation=evaluation)

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------

    def _extract_job_data(self, job: Any) -> Dict[str, Any]:
        if isinstance(job, dict):
            title = self._safe_str(job.get("title") or job.get("job_title"))
            description = self._safe_str(job.get("description") or job.get("job_description"))
            skills = job.get("skills") or []
        else:
            title = self._safe_str(
                getattr(job, "title", None) or getattr(job, "job_title", None)
            )
            description = self._safe_str(
                getattr(job, "description", None) or getattr(job, "job_description", None)
            )
            skills = getattr(job, "skills", []) or []

        if not isinstance(skills, list):
            skills = [str(skills)]

        return {
            "title": title.strip(),
            "description": description.strip(),
            "skills": [self._safe_str(x).strip() for x in skills if self._safe_str(x).strip()],
        }

    def _extract_evaluation_data(self, evaluation: Any) -> Dict[str, Any]:
        if isinstance(evaluation, dict):
            score = self._to_int(evaluation.get("score"), 0)
            win_probability = self._to_int(evaluation.get("win_probability"), 0)
            confidence = self._safe_str(evaluation.get("confidence") or "MEDIUM").upper()
            proposal_mode = self._safe_str(evaluation.get("proposal_mode") or "STANDARD").upper()
            reasons = evaluation.get("reasons") or []
            risks = evaluation.get("risks") or []
        else:
            score = self._to_int(getattr(evaluation, "score", 0), 0)
            win_probability = self._to_int(getattr(evaluation, "win_probability", 0), 0)
            confidence = self._safe_str(getattr(evaluation, "confidence", "MEDIUM")).upper()
            proposal_mode = self._safe_str(
                getattr(evaluation, "proposal_mode", "STANDARD")
            ).upper()
            reasons = getattr(evaluation, "reasons", []) or []
            risks = getattr(evaluation, "risks", []) or []

        return {
            "score": score,
            "win_probability": win_probability,
            "confidence": confidence,
            "proposal_mode": proposal_mode,
            "reasons": [self._safe_str(x).strip() for x in reasons if self._safe_str(x).strip()],
            "risks": [self._safe_str(x).strip() for x in risks if self._safe_str(x).strip()],
        }

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_cover_letter(
        self,
        title: str,
        strengths: List[str],
        focus_points: List[str],
        score: int,
        win_probability: int,
        confidence: str,
        mode: str = "STANDARD",
    ) -> str:
        opening = self._build_opening(title, focus_points, mode)
        platform_background = self._build_platform_background(mode)
        credibility = self._build_credibility_summary(strengths, mode)
        closing = self._build_closing(score, win_probability, confidence, mode)
        return "\n\n".join([opening, platform_background, credibility, closing]).strip()

    def _build_opening(self, title: str, focus_points: List[str], mode: str) -> str:
        project_ref = f"your project: {title}" if title else "this type of project"

        if mode.upper() == "PREMIUM":
            return (
                f"Hi,\n\n"
                f"I understand that you are not just looking for someone to complete {project_ref}, "
                f"but for someone who can turn the requirements into a reliable, production-ready solution. "
                f"My focus is always on building something that is accurate, maintainable, and genuinely useful in practice.\n\n"
                f"From the job description, the key priorities appear to be: "
                f"{self._format_inline_list(focus_points)}."
            )

        return (
            f"Hi,\n\n"
            f"I’ve done exactly this type of project before—recently building Python automation and data workflows designed for reliable outputs, easier maintenance, and cleaner delivery.\n\n"
            f"For this project, the main priorities I see are: {self._format_inline_list(focus_points)}."
        )


    def _build_platform_background(self, mode: str) -> str:
        return self.PLATFORM_EXPERIENCE_PARAGRAPH

    def _build_credibility_summary(self, strengths: List[str], mode: str) -> str:
        """
        Keep this short to avoid repeating the full experience section.
        """
        if mode.upper() == "PREMIUM":
            return (
                "My background is strongest in Python-based backend work, automation workflows, "
                "clean structured outputs, and maintainable implementation. "
                "I focus on building solutions that are dependable in production and easy to extend after handover."
            )

        return (
            "I have relevant experience in Python development, automation, structured outputs, "
            "and practical delivery for real-world workflows."
        )

    def _build_closing(
        self,
        score: int,
        win_probability: int,
        confidence: str,
        mode: str,
    ) -> str:
        if mode.upper() == "PREMIUM":
            return (
                "I would structure the work carefully from the beginning so the solution is not only delivered quickly, "
                "but is also easy to test, refine, and integrate into your broader workflow.\n\n"
                "If selected, I can provide clean implementation, clear communication throughout the build, "
                "and a practical handover at the end."
            )

        return (
            "I can deliver this in a clean and professional way, with attention to reliability, clear outputs, "
            "and practical implementation.\n\n"
            "I would be glad to discuss the exact scope and the expected deliverable format."
        )

    def _build_relevant_experience(
        self,
        strengths: List[str],
        keywords: str,
        premium: bool = False,
    ) -> str:
        blocks: List[str] = ["Relevant experience:"]

        seen = set()

        def add_line(line: str) -> None:
            normalized = line.strip().lower()
            if normalized and normalized not in seen:
                seen.add(normalized)
                blocks.append(f"- {line}")

        for item in strengths[:5]:
            add_line(item)

        if "scrap" in keywords or "extract" in keywords or "crawl" in keywords:
            add_line(
                "Strong hands-on experience with Python scraping stacks including Playwright, Selenium, BeautifulSoup, and structured export pipelines."
            )

        if "api" in keywords or "fastapi" in keywords or "backend" in keywords:
            add_line(
                "Experience debugging backend logic, improving validation, standardizing outputs, and making API behavior more reliable."
            )

        if "streamlit" in keywords or "dashboard" in keywords or "ui" in keywords:
            add_line(
                "Experience building practical Python interfaces and decision-support tools with clear user-facing outputs."
            )

        if any(k in keywords for k in ["deploy", "hosting", "cloud", "aws", "render", "railway"]):
            add_line(
                "Experience preparing Python projects for deployment, including practical structure, configuration, and handover readiness."
            )

        if premium:
            add_line(
                "I typically build with maintainability in mind, so future changes can be made without rewriting core logic."
            )

        return "\n".join(blocks).strip()

    def _build_approach(
        self,
        focus_points: List[str],
        deliverables: List[str],
        risks: List[str],
        mode: str = "STANDARD",
    ) -> str:
        lines: List[str] = ["Approach:"]

        if mode.upper() == "PREMIUM":
            lines.append("- Review the existing logic, structure, and expected output behavior.")
            lines.append("- Confirm the exact success criteria and identify edge cases early.")
            lines.append("- Implement the core solution with clean, modular code.")
            lines.append("- Validate outputs against real examples and refine weak points.")
            lines.append("- Deliver a result that is easy to test, extend, and hand over.")
        else:
            lines.append("- Review requirements and confirm the expected output format.")
            lines.append("- Implement the solution in a clean and reliable way.")
            lines.append("- Test the main flow and edge cases.")
            lines.append("- Deliver code and outputs in a practical handover-ready format.")

        if focus_points:
            lines.append("")
            lines.append("Key areas of focus:")
            for item in focus_points[:4]:
                lines.append(f"- {item}")

        if deliverables:
            lines.append("")
            lines.append("Expected deliverables:")
            for item in deliverables[:5]:
                lines.append(f"- {item}")

        if risks:
            lines.append("")
            lines.append("Areas I would clarify early:")
            for item in risks[:3]:
                lines.append(f"- {self._normalize_risk_to_question(item)}")

        return "\n".join(lines).strip()

    # ------------------------------------------------------------------
    # Content selection
    # ------------------------------------------------------------------

    def _select_relevant_strengths(self, keywords: str) -> List[str]:
        strengths: List[str] = []

        if any(k in keywords for k in ["python", "fastapi", "flask", "backend", "api"]):
            strengths.append(
                "Strong Python development experience, including backend logic, validation, API workflows, and production-oriented code structure."
            )

        if any(k in keywords for k in ["scrap", "crawler", "crawl", "extract", "data collection"]):
            strengths.append(
                "Extensive experience building data extraction and web scraping systems, including handling dynamic pages, structured outputs, and workflow reliability."
            )

        if any(k in keywords for k in ["streamlit", "dashboard", "web app", "frontend", "ui"]):
            strengths.append(
                "Experience turning Python logic into usable interfaces and lightweight web applications with clear inputs and outputs."
            )

        if any(k in keywords for k in ["automation", "workflow", "pipeline", "integration"]):
            strengths.append(
                "Experience building automation workflows and integrating multiple components into stable end-to-end systems."
            )

        if any(k in keywords for k in ["csv", "excel", "xlsx", "json", "dataset", "report"]):
            strengths.append(
                "Strong focus on structured output quality, including clean CSV, Excel, JSON, and reporting-oriented deliverables."
            )

        if any(k in keywords for k in ["playwright", "selenium", "beautifulsoup", "requests", "httpx"]):
            strengths.append(
                "Hands-on experience with practical Python tooling such as Playwright, Selenium, BeautifulSoup, Requests, and HTTP-based extraction workflows."
            )

        if any(k in keywords for k in ["deploy", "hosting", "render", "railway", "cloud", "aws"]):
            strengths.append(
                "Experience preparing Python projects for deployment, including practical structure, configuration, and handover readiness."
            )

        if any(k in keywords for k in ["ai", "llm", "analysis", "intelligence", "scoring"]):
            strengths.append(
                "Experience building decision-support and intelligence-style tools that turn raw inputs into usable recommendations and outputs."
            )

        if not strengths:
            strengths.append(
                "I specialize in building practical Python solutions with strong attention to reliability, maintainability, and clean delivery."
            )
            strengths.append(
                "My work typically focuses on turning unclear requirements into structured, working solutions that are usable in real operations."
            )

        return strengths

    def _select_focus_points(self, keywords: str) -> List[str]:
        points: List[str] = []

        if any(k in keywords for k in ["debug", "fix", "issue", "bug"]):
            points.append("improving the current logic and removing the root causes of inconsistent behavior")

        if any(k in keywords for k in ["validation", "error handling", "response", "api"]):
            points.append("improving validation, error handling, and output consistency")

        if any(k in keywords for k in ["performance", "optimize", "speed", "scale", "scaling"]):
            points.append("optimizing performance where the current implementation is inefficient")

        if any(k in keywords for k in ["scrap", "extract", "crawler", "crawl"]):
            points.append("building reliable extraction logic and structured output handling")

        if any(k in keywords for k in ["streamlit", "ui", "web app", "frontend"]):
            points.append("making the tool easy to use through a clear interface")

        if any(k in keywords for k in ["integration", "webhook", "crm", "activecampaign"]):
            points.append("keeping the architecture clean for integration with external systems")

        if any(k in keywords for k in ["deploy", "cloud", "aws", "hosting"]):
            points.append("keeping deployment and handover practical for production use")

        if not points:
            points.append("delivering a clean and reliable implementation")
            points.append("keeping the solution maintainable for future updates")

        return points

    def _select_deliverables(self, keywords: str) -> List[str]:
        items: List[str] = []

        if any(k in keywords for k in ["api", "fastapi", "backend"]):
            items.append("improved backend behavior with cleaner response structure")

        if any(k in keywords for k in ["validation", "error handling"]):
            items.append("proper validation and clearer handling of failed or incomplete cases")

        if any(k in keywords for k in ["streamlit", "web app", "ui"]):
            items.append("a practical user-facing interface for the core workflow")

        if any(k in keywords for k in ["deploy", "hosting", "render", "railway", "cloud", "aws"]):
            items.append("deployment-ready project structure and handover guidance")

        if any(k in keywords for k in ["csv", "xlsx", "json", "report"]):
            items.append("clean, structured outputs ready for use")

        if any(k in keywords for k in ["integration", "api", "webhook", "crm"]):
            items.append("integration-ready architecture for the next project stage")

        if not items:
            items.append("clean source code")
            items.append("reliable implementation")
            items.append("practical handover-ready result")

        return items

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_keyword_blob(self, title: str, description: str, skills: List[str]) -> str:
        return " ".join([title, description, " ".join(skills)]).lower()

    def _join_sections(self, cover_letter: str, relevant_experience: str, approach: str) -> str:
        return "\n\n".join(
            [
                cover_letter.strip(),
                relevant_experience.strip(),
                approach.strip(),
            ]
        ).strip()

    def _format_inline_list(self, items: List[str]) -> str:
        clean = [i.strip() for i in items if i and i.strip()]
        if not clean:
            return "reliability, clean implementation, and practical delivery"
        if len(clean) == 1:
            return clean[0]
        if len(clean) == 2:
            return f"{clean[0]} and {clean[1]}"
        return ", ".join(clean[:-1]) + f", and {clean[-1]}"

    def _normalize_risk_to_question(self, risk: str) -> str:
        text = risk.strip()
        if not text:
            return "confirm open project details"

        lowered = text.lower()

        if "scope" in lowered:
            return "confirm the exact scope boundaries"
        if "output format" in lowered:
            return "confirm the preferred output format and structure"
        if "limited job detail" in lowered or "unclear" in lowered:
            return "clarify the missing technical details before implementation"
        if "timeline" in lowered:
            return "confirm deadline expectations and milestones"
        if "target website not specified" in lowered:
            return "confirm the target website, source structure, and any access limitations"

        return text[0].upper() + text[1:] if text else "clarify key project details"

    def _soften_scope_claims(self, text: str) -> str:
        replacements = {
            "I understand that you are not just looking for someone to complete": "It looks like you are looking for someone to complete",
            "the key priorities appear to be": "the main priorities seem to be",
        }
        updated = text
        for old, new in replacements.items():
            updated = updated.replace(old, new)
        return updated

    def _safe_str(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value)

    def _to_int(self, value: Any, default: int = 0) -> int:
        try:
            if value is None:
                return default
            if isinstance(value, bool):
                return int(value)
            return int(round(float(value)))
        except (TypeError, ValueError):
            return default
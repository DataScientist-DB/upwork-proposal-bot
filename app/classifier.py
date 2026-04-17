from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from rules import STRONG_KEYWORDS


class JobClassifier:
    def classify(self, job_text: str) -> Dict[str, List[str] | str | dict]:
        text = job_text.lower()
        scores = defaultdict(int)
        matches = defaultdict(list)

        for category, keywords in STRONG_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    scores[category] += 1
                    matches[category].append(keyword)

        if not scores:
            return {
                "primary_category": "general",
                "matched_categories": {},
                "matched_keywords": []
            }

        primary_category = max(scores, key=scores.get)
        matched_keywords = sorted({kw for kws in matches.values() for kw in kws})

        return {
            "primary_category": primary_category,
            "matched_categories": dict(scores),
            "matched_keywords": matched_keywords,
        }
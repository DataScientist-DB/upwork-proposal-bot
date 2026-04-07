from __future__ import annotations


class JobStrategy:
    def decide(self, evaluation: dict, meta: dict) -> dict:
        scores = evaluation.get("scores", {})
        total = scores.get("total", 0)

        proposals = meta.get("proposals", 0)
        last_viewed_hours = meta.get("last_viewed_hours", 0)
        interviewing = meta.get("interviewing", 0)
        invites_sent = meta.get("invites_sent", 0)
        unanswered_invites = meta.get("unanswered_invites", 0)
        avg_bid = meta.get("avg_bid", 0)
        high_bid = meta.get("high_bid", 0)
        low_bid = meta.get("low_bid", 0)

        high_competition = proposals >= 30
        very_high_competition = proposals >= 50
        many_interviews = interviewing >= 5
        client_not_fresh = last_viewed_hours >= 6
        slow_client = invites_sent >= 10 and unanswered_invites >= 5

        # Default safe strategy so keys always exist
        strategy = {
            "decision": "apply",
            "proposal_type": "standard",
            "effort": "medium",
            "positioning": "competitive",
            "strategy_note": "Reasonable fit with normal proposal effort.",
        }

        if total < 14:
            strategy.update({
                "decision": "skip",
                "proposal_type": "standard",
                "effort": "low",
                "positioning": "safe",
                "strategy_note": "Low overall fit score; better to skip and protect application ROI.",
            })
            return strategy

        if total >= 20:
            strategy.update({
                "decision": "apply",
                "proposal_type": "premium",
                "effort": "high",
                "positioning": "premium",
                "strategy_note": "Strong fit; worth a premium-quality proposal.",
            })

        if 14 <= total < 20:
            strategy.update({
                "decision": "apply",
                "proposal_type": "standard",
                "effort": "medium",
                "positioning": "competitive",
                "strategy_note": "Moderate fit; standard proposal is the right level.",
            })

        # Market-aware override:
        # high competition + many interviews => do not overinvest, use short sharp proposal
        if high_competition or many_interviews or client_not_fresh or slow_client:
            strategy.update({
                "decision": "apply" if total >= 15 else "skip",
                "proposal_type": "short" if total >= 15 else "standard",
                "effort": "low" if total >= 15 else "low",
                "positioning": "premium" if total >= 20 else "selective",
                "strategy_note": "Crowded job / active competition; use a shorter, sharper proposal and avoid overinvesting.",
            })

        # Pricing-aware adjustment
        if avg_bid >= 80 or high_bid >= 150:
            if strategy["decision"] == "apply" and total >= 18:
                strategy["positioning"] = "premium"
                if strategy["proposal_type"] != "short":
                    strategy["proposal_type"] = "premium"
                strategy["strategy_note"] += " Bid range supports stronger positioning."

        # Very crowded jobs: keep it short unless fit is exceptional
        if very_high_competition and total < 22 and strategy["decision"] == "apply":
            strategy["proposal_type"] = "short"
            strategy["effort"] = "low"
            strategy["strategy_note"] += " Very high proposal count favors brevity."

        # Keep low/avg/high available if you want to inspect later
        strategy["market_context"] = {
            "proposals": proposals,
            "last_viewed_hours": last_viewed_hours,
            "interviewing": interviewing,
            "invites_sent": invites_sent,
            "unanswered_invites": unanswered_invites,
            "avg_bid": avg_bid,
            "high_bid": high_bid,
            "low_bid": low_bid,
        }

        return strategy
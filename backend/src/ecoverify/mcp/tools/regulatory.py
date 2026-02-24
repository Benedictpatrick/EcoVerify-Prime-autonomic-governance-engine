"""Regulatory Registry MCP tools.

Queries an in-memory EU AI Act (2026 v2) knowledge base and evaluates
compliance vectors for autonomous actions.
"""

from __future__ import annotations

import json
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent / "data"
_eu_ai_act: list[dict] | None = None


def _load_eu_ai_act() -> list[dict]:
    global _eu_ai_act
    if _eu_ai_act is None:
        path = _DATA_DIR / "EU_AI_Act_v2.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _eu_ai_act = data.get("articles", data) if isinstance(data, dict) else data
    return _eu_ai_act


def register_regulatory_tools(mcp):
    """Register EU AI Act compliance tools on the given FastMCP server instance."""

    @mcp.tool()
    def query_eu_ai_act(section: str = "", keyword: str = "") -> dict:
        """Query the EU AI Act (2026 v2) regulatory database.

        Returns matching articles/sections. Provide either a section number
        (e.g. 'Article 14') or a keyword (e.g. 'transparency').
        """
        articles = _load_eu_ai_act()
        results = []

        for article in articles:
            match = False
            if section and section.lower() in article.get("section", "").lower():
                match = True
            if keyword:
                searchable = (
                    article.get("title", "")
                    + " "
                    + article.get("text", "")
                    + " "
                    + " ".join(article.get("keywords", []))
                ).lower()
                if keyword.lower() in searchable:
                    match = True
            if not section and not keyword:
                match = True  # return all if no filter
            if match:
                results.append(article)

        return {
            "query": {"section": section, "keyword": keyword},
            "result_count": len(results),
            "articles": results[:10],  # cap for LLM context
        }

    @mcp.tool()
    def check_compliance_vector(
        action_description: str,
        risk_level: str = "high",
    ) -> dict:
        """Evaluate an action against EU AI Act compliance vectors.

        Risk levels: minimal, limited, high, unacceptable.
        Returns a compliance verdict with relevant articles and reasoning.
        """
        articles = _load_eu_ai_act()

        # Map risk levels to relevant article categories
        risk_articles: dict[str, list[str]] = {
            "unacceptable": ["Article 5"],
            "high": ["Article 6", "Article 9", "Article 13", "Article 14", "Article 52"],
            "limited": ["Article 52"],
            "minimal": [],
        }

        relevant_sections = risk_articles.get(risk_level.lower(), [])
        relevant = [
            a for a in articles
            if any(sec.lower() in a.get("section", "").lower() for sec in relevant_sections)
        ]

        # Determine compliance based on risk level and transparency requirements
        requires_human_oversight = risk_level.lower() in ("high", "unacceptable")
        requires_transparency = risk_level.lower() in ("high", "limited")

        compliant = True
        reasoning_parts = []

        if risk_level.lower() == "unacceptable":
            compliant = False
            reasoning_parts.append(
                "Action classified as unacceptable risk under Article 5 — prohibited."
            )
        elif risk_level.lower() == "high":
            reasoning_parts.append(
                "Action classified as high-risk AI system. "
                "Must satisfy Articles 6, 9 (risk management), 13 (transparency), "
                "14 (human oversight), and 52 (transparency obligations)."
            )
            if "autonomous" in action_description.lower():
                reasoning_parts.append(
                    "Autonomous decision-making detected — human oversight (Article 14) "
                    "is mandatory before execution."
                )
        elif risk_level.lower() == "limited":
            reasoning_parts.append(
                "Limited risk classification. Transparency obligations apply (Article 52)."
            )
        else:
            reasoning_parts.append("Minimal risk — no specific obligations under EU AI Act.")

        return {
            "compliant": compliant,
            "risk_classification": risk_level,
            "requires_human_oversight": requires_human_oversight,
            "requires_transparency": requires_transparency,
            "relevant_articles": [
                {"section": a["section"], "title": a["title"]} for a in relevant
            ],
            "reasoning": " ".join(reasoning_parts),
            "action_evaluated": action_description,
        }

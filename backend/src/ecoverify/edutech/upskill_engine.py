"""Just-in-time upskill engine — generates contextual micro-lessons.

When cognitive friction is detected, this module creates targeted training
recommendations based on the compliance gap, agent phase, and operator
interaction patterns.  Uses GPT-4o when available, deterministic fallback otherwise.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ecoverify.edutech.models import FrictionSignal, UpskillRecommendation

logger = logging.getLogger(__name__)

# ── Deterministic micro-lesson library ──────────────────────────

_LESSON_DB: dict[str, dict] = {
    "slow_approval": {
        "topic": "Understanding ROI Metrics in Energy Optimization",
        "content": (
            "When reviewing energy optimization proposals, focus on three key metrics:\n"
            "1. **Monthly Savings** — direct operational cost reduction.\n"
            "2. **NPV (3yr)** — accounts for time value of money at 8% discount rate.\n"
            "3. **Payback Period** — months until the investment is recovered.\n\n"
            "💡 Tip: If the payback period is <12 months and NPV is positive, "
            "the action is almost always worth approving."
        ),
        "articles": ["EU AI Act Art. 14 — Human Oversight", "ASHRAE 90.1 — Energy Standards"],
        "minutes": 3,
    },
    "repeated_rejection": {
        "topic": "Compliance Thresholds and Action Boundaries",
        "content": (
            "If you're repeatedly rejecting agent recommendations, consider:\n"
            "1. Are the anomaly severity thresholds too sensitive? Adjust via the ROI slider.\n"
            "2. Is the compliance framework overly strict? Check the Articles referenced.\n"
            "3. Has the risk profile changed? Review the latest fintech risk score.\n\n"
            "💡 Tip: Use the ROI adjustment slider to fine-tune recommendations "
            "before rejecting outright."
        ),
        "articles": ["EU AI Act Art. 9 — Risk Management", "ISO 50001 — Energy Management"],
        "minutes": 4,
    },
    "self_correction_loop": {
        "topic": "Data Citation and Source Verification",
        "content": (
            "Self-correction loops occur when the Jurist cannot verify data citations.\n"
            "This usually indicates:\n"
            "1. Telemetry data gaps — check BMS sensor connectivity.\n"
            "2. Citation format issues — ensure data sources are properly tagged.\n"
            "3. Threshold misconfiguration — anomaly thresholds may be too tight.\n\n"
            "💡 Tip: The 'Cite-Before-Act' protocol requires every decision to "
            "reference verifiable data sources."
        ),
        "articles": ["EU AI Act Art. 13 — Transparency", "EU AI Act Art. 71 — Auditing"],
        "minutes": 5,
    },
    "high_error_rate": {
        "topic": "System Health and Error Diagnosis",
        "content": (
            "High error rates suggest systemic issues:\n"
            "1. Check BMS telemetry connectivity and data freshness.\n"
            "2. Review recent infrastructure changes that may affect baseline readings.\n"
            "3. Consider running a manual diagnostic scan before triggering automated analysis.\n\n"
            "💡 Tip: The error log in the Decision Traces panel shows detailed failure reasons."
        ),
        "articles": ["ISO 27001 — Information Security", "NIST AI 600-1 — AI Risk"],
        "minutes": 3,
    },
}


def generate_upskill(friction_signals: list[FrictionSignal]) -> list[UpskillRecommendation]:
    """Generate upskill recommendations for detected friction signals.

    Uses deterministic lesson database.  When LLM is enabled, supplements
    with GPT-4o-generated contextual guidance.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    recommendations: list[UpskillRecommendation] = []

    for signal in friction_signals:
        lesson = _LESSON_DB.get(signal.signal_type)
        if not lesson:
            continue

        urgency = "required" if signal.severity == "high" else "recommended" if signal.severity == "medium" else "suggested"

        rec = UpskillRecommendation(
            topic=lesson["topic"],
            urgency=urgency,
            content=lesson["content"],
            related_articles=lesson["articles"],
            estimated_minutes=lesson["minutes"],
            timestamp=now_iso,
        )
        recommendations.append(rec)

    # Optionally enrich with LLM
    _try_llm_enrichment(recommendations, friction_signals)

    return recommendations


def _try_llm_enrichment(
    recommendations: list[UpskillRecommendation],
    signals: list[FrictionSignal],
) -> None:
    """Attempt to enrich recommendations with LLM-generated context."""
    try:
        from ecoverify.agents.llm import get_chat_model, is_llm_enabled
        if not is_llm_enabled():
            return

        model = get_chat_model()
        if model is None:
            return

        # Generate a contextual summary for the first signal
        if signals and recommendations:
            signal = signals[0]
            prompt = (
                f"An EcoVerify operator experienced '{signal.signal_type}' cognitive friction "
                f"during the '{signal.agent_phase}' phase. Context: {signal.context}\n\n"
                f"Provide a 2-sentence actionable tip to help them understand and resolve this situation."
            )
            response = model.invoke(prompt)
            if response and response.content:
                recommendations[0].content += f"\n\n🤖 **AI Insight**: {response.content}"
    except Exception as e:
        logger.debug("LLM enrichment skipped: %s", e)

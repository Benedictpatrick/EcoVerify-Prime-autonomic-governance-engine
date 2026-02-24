"""Conditional edge routing logic for the EcoVerify graph.

Each function inspects the current ``EcoVerifyState`` and returns the name
of the next node (or ``END``).  The graph uses these as conditional edges
to implement:

  - Self-correction loop: JURIST → VANGUARD (citation failure)
  - Adjustment loop:      GOVERNOR → ARCHITECT (ROI re-simulation)
  - Happy path:           VANGUARD → JURIST → ARCHITECT → GOVERNOR → FINALIZE
"""

from __future__ import annotations

import logging

from ecoverify.agents.state import EcoVerifyState

logger = logging.getLogger(__name__)

# Maximum allowed self-correction iterations to prevent runaway loops.
MAX_ITERATIONS = 5


def route_after_vanguard(state: EcoVerifyState) -> str:
    """After VANGUARD: route to JURIST if anomalies found, else END."""
    anomalies = state.get("anomalies", [])
    if anomalies:
        logger.info("VANGUARD → JURIST (%d anomalies detected)", len(anomalies))
        return "jurist"
    logger.info("VANGUARD → END (no anomalies)")
    return "__end__"


def route_after_jurist(state: EcoVerifyState) -> str:
    """After JURIST: route based on citation validity and compliance.

    - Citation failure → VANGUARD (self-correction loop, max 5 iterations)
    - Compliant + anomalies → ARCHITECT
    - Non-compliant → GOVERNOR (immediate human review)
    """
    phase = state.get("current_phase", "")
    iteration_count = state.get("iteration_count", 0)

    # Self-correction loop for citation failures
    if phase == "citation_failure":
        if iteration_count >= MAX_ITERATIONS:
            logger.warning("Max self-correction iterations reached. Forcing END.")
            return "__end__"
        logger.info("JURIST → VANGUARD (citation failure, iteration %d)", iteration_count)
        return "vanguard"

    compliance = state.get("compliance_report", {})
    status = compliance.get("status", "unknown")

    if status == "non_compliant":
        logger.info("JURIST → GOVERNOR (non-compliant — immediate human review)")
        return "governor"

    logger.info("JURIST → ARCHITECT (compliant)")
    return "architect"


def route_after_architect(state: EcoVerifyState) -> str:
    """After ARCHITECT: always route to GOVERNOR (HITL is mandatory for state mutations)."""
    logger.info("ARCHITECT → GOVERNOR (mandatory HITL checkpoint)")
    return "governor"


# Note: GOVERNOR routing is handled internally via LangGraph's Command(goto=...)
# so no route_after_governor function is needed here.  The governor_node returns
# Command(goto="finalize") or Command(goto="architect") directly.

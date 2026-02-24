"""THE GOVERNOR — mandatory Human-in-the-Loop breakpoint.

Responsibilities:
  1. Pause execution via LangGraph ``interrupt()`` for state-mutating actions.
  2. Present the Governor panel UI (action summary, ROI, approval controls).
  3. On resume, either proceed to finalisation or loop back to ARCHITECT with
     adjusted ROI parameters.
  4. Sign governor decision with NHI.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from langchain_core.messages import AIMessage
from langgraph.types import Command, interrupt

from ecoverify.agents.state import EcoVerifyState
from ecoverify.nhi.keys import load_private_key, generate_agent_keypair
from ecoverify.nhi.signing import sign_decision_trace
from ecoverify.telemetry.tracing import agent_span

logger = logging.getLogger(__name__)


@agent_span("governor_node")
def governor_node(state: EcoVerifyState) -> Command:
    """HITL node — pause for human approval before executing verified actions."""

    now_iso = datetime.now(timezone.utc).isoformat()
    simulation = state.get("simulation_result", {})
    anomalies = state.get("anomalies", [])
    compliance = state.get("compliance_report", {})
    jira_tickets = state.get("jira_tickets", [])

    action_summary = (
        f"Approve maintenance action for {len(anomalies)} anomalie(s). "
        f"Estimated monthly saving: ${simulation.get('monthly_savings_usd', 0):,.2f}. "
        f"CO₂ reduction: {simulation.get('co2_tons_saved_annual', 0):.1f} tons/yr ({simulation.get('env_reduction_pct', 0)}%). "
        f"Compliance status: {compliance.get('status', 'unknown')}. "
        f"Jira tickets to submit: {len(jira_tickets)}."
    )

    # ── Emit UI event BEFORE interrupt (will be captured by streaming) ──
    ui_pre = [
        {
            "type": "governor_panel",
            "action_summary": action_summary,
            "estimated_roi": simulation.get("monthly_savings_usd", 0),
            "npv_3yr": simulation.get("npv_3yr_usd", 0),
            "payback_months": simulation.get("payback_months", 0),
            "co2_tons_saved_annual": simulation.get("co2_tons_saved_annual", 0),
            "env_reduction_pct": simulation.get("env_reduction_pct", 0),
            "campus_buildings": simulation.get("campus_buildings", 1),
            "requires_approval": True,
            "timestamp": now_iso,
        },
        {
            "type": "neural_feed",
            "agent": "GOVERNOR",
            "message": "⏳ Awaiting human approval for state-mutating action…",
            "severity": "medium",
            "timestamp": now_iso,
        },
    ]

    # ── INTERRUPT — execution pauses here until human resumes ──
    human_response = interrupt({
        "action_summary": action_summary,
        "estimated_roi": simulation.get("monthly_savings_usd", 0),
        "requires_approval": True,
        "ui_events": ui_pre,
    })

    # ── Process human response ──────────────────────────
    approved = human_response.get("approved", False) if isinstance(human_response, dict) else bool(human_response)
    roi_adjustment = human_response.get("roi_adjustment", 1.0) if isinstance(human_response, dict) else 1.0

    # ── NHI signing ─────────────────────────────────────
    try:
        pk = load_private_key("governor")
    except FileNotFoundError:
        pk, _ = generate_agent_keypair("governor")

    trace = sign_decision_trace(
        agent_id="governor",
        decision={
            "action": "human_approval",
            "approved": approved,
            "roi_adjustment": roi_adjustment,
        },
        private_key=pk,
    )

    if approved:
        return Command(
            goto="finalize",
            update={
                "governor_approval": True,
                "current_phase": "governor_approved",
                "decision_traces": [trace.model_dump()],
                "ui_events": [
                    {
                        "type": "neural_feed",
                        "agent": "GOVERNOR",
                        "message": "✅ Action APPROVED by human operator.",
                        "severity": "low",
                        "timestamp": now_iso,
                    },
                ],
                "messages": [
                    AIMessage(
                        content="[GOVERNOR] Human operator approved the action. Proceeding to finalisation.",
                        name="governor",
                    )
                ],
            },
        )
    else:
        # Loop back to ARCHITECT with adjusted ROI
        return Command(
            goto="architect",
            update={
                "governor_approval": False,
                "current_phase": "governor_rejected",
                "decision_traces": [trace.model_dump()],
                "simulation_result": {
                    **simulation,
                    "roi_adjustment": roi_adjustment,
                },
                "ui_events": [
                    {
                        "type": "neural_feed",
                        "agent": "GOVERNOR",
                        "message": f"❌ Action REJECTED. Re-simulating with ROI adjustment ×{roi_adjustment:.2f}.",
                        "severity": "medium",
                        "timestamp": now_iso,
                    },
                ],
                "messages": [
                    AIMessage(
                        content=f"[GOVERNOR] Action rejected. Re-routing to ARCHITECT with ROI adjustment {roi_adjustment}.",
                        name="governor",
                    )
                ],
            },
        )

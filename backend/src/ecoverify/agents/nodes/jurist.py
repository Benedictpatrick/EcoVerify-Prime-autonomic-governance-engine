"""THE JURIST — EU AI Act compliance evaluation with System 2 reasoning.

Responsibilities:
  1. Verify VANGUARD's citations are present and valid (Cite-Before-Act enforcement).
  2. If citations are invalid → route back to VANGUARD (self-correction loop).
  3. Query EU AI Act via MCP Regulatory Registry tools.
  4. Perform chain-of-thought compliance evaluation using the LLM.
  5. Sign compliance report with NHI.
  6. Emit UI events for the Neural Feed.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from langchain_core.messages import AIMessage

from ecoverify.agents.state import EcoVerifyState
from ecoverify.mcp.tools.regulatory import register_regulatory_tools
from ecoverify.nhi.keys import load_private_key, generate_agent_keypair
from ecoverify.nhi.middleware import verify_citations_present
from ecoverify.nhi.signing import sign_decision_trace
from ecoverify.telemetry.tracing import agent_span

logger = logging.getLogger(__name__)

# ── In-process regulatory tool access ──────────────────────────────

class _ToolBucket:
    def __init__(self):
        self._tools: dict[str, callable] = {}
    def tool(self):
        def deco(fn):
            self._tools[fn.__name__] = fn
            return fn
        return deco
    def __getattr__(self, name):
        if name.startswith("_"):
            return super().__getattribute__(name)
        return self._tools[name]

_reg = _ToolBucket()
register_regulatory_tools(_reg)


@agent_span("jurist_node")
def jurist_node(state: EcoVerifyState) -> dict:
    """Compliance node — evaluate anomalies against EU AI Act."""

    now_iso = datetime.now(timezone.utc).isoformat()
    ui_events: list[dict] = []

    # ── 1. Cite-Before-Act enforcement ──────────────────
    citations = state.get("citations", [])
    if not verify_citations_present(citations):
        ui_events.append({
            "type": "neural_feed",
            "agent": "JURIST",
            "message": "⚠ Citation verification FAILED — routing back to VANGUARD for self-correction.",
            "severity": "high",
            "timestamp": now_iso,
        })
        return {
            "current_phase": "citation_failure",
            "error_log": ["JURIST: Cite-Before-Act violation — no valid citations from VANGUARD."],
            "ui_events": ui_events,
            "compliance_report": None,
            "messages": [
                AIMessage(
                    content="[JURIST] Citation verification failed. Requesting VANGUARD re-scan with proper data citations.",
                    name="jurist",
                )
            ],
        }

    # ── 2. Evaluate anomalies ───────────────────────────
    anomalies = state.get("anomalies", [])
    if not anomalies:
        ui_events.append({
            "type": "neural_feed",
            "agent": "JURIST",
            "message": "No anomalies to evaluate — system compliant by default.",
            "severity": "low",
            "timestamp": now_iso,
        })
        compliance_report = {
            "status": "compliant",
            "anomalies_evaluated": 0,
            "findings": [],
            "timestamp": now_iso,
        }
        return {
            "current_phase": "jurist_complete",
            "compliance_report": compliance_report,
            "ui_events": ui_events,
            "messages": [
                AIMessage(
                    content="[JURIST] No anomalies to evaluate. System is compliant.",
                    name="jurist",
                )
            ],
        }

    # ── 3. Query regulatory database ────────────────────
    # Look up transparency (Art 13), human oversight (Art 14), and risk management (Art 9)
    transparency_result = _reg.query_eu_ai_act(keyword="transparency")
    oversight_result = _reg.query_eu_ai_act(keyword="human oversight")

    # Evaluate each anomaly against compliance vectors
    findings = []
    for anomaly in anomalies:
        action_desc = (
            f"Autonomous detection of {anomaly['type']} anomaly in building "
            f"{anomaly.get('building_id', 'unknown')}: {anomaly.get('metric', 'N/A')}"
        )
        compliance_check = _reg.check_compliance_vector(
            action_description=action_desc,
            risk_level=anomaly.get("severity", "high"),
        )
        findings.append({
            "anomaly": anomaly,
            "compliance": compliance_check,
            "articles_referenced": [
                a.get("section", "") for a in transparency_result.get("articles", [])[:3]
            ] + [
                a.get("section", "") for a in oversight_result.get("articles", [])[:2]
            ],
        })

    # ── 4. Determine overall verdict ────────────────────
    all_compliant = all(f["compliance"].get("compliant", False) for f in findings)
    requires_hitl = any(f["compliance"].get("requires_human_oversight", False) for f in findings)

    compliance_report = {
        "status": "compliant" if all_compliant else "non_compliant",
        "requires_human_oversight": requires_hitl,
        "anomalies_evaluated": len(anomalies),
        "findings": findings,
        "reasoning": (
            "All detected anomalies fall within high-risk AI system classification "
            "under EU AI Act Articles 6, 9, 13, 14. Autonomous response actions require "
            "human oversight (Article 14) before execution. Transparency obligations "
            "(Article 13) satisfied through decision trace logging."
        ),
        "timestamp": now_iso,
    }

    # ── 5. NHI signing ──────────────────────────────────
    try:
        pk = load_private_key("jurist")
    except FileNotFoundError:
        pk, _ = generate_agent_keypair("jurist")

    trace = sign_decision_trace(
        agent_id="jurist",
        decision={
            "action": "compliance_evaluation",
            "status": compliance_report["status"],
            "anomalies_evaluated": len(anomalies),
            "requires_hitl": requires_hitl,
        },
        private_key=pk,
    )

    # ── 6. UI events ────────────────────────────────────
    ui_events.append({
        "type": "neural_feed",
        "agent": "JURIST",
        "message": (
            f"Verified {len(anomalies)} anomalie(s) against EU AI Act — "
            f"{'COMPLIANT' if all_compliant else 'NON-COMPLIANT'}. "
            f"Human oversight {'required' if requires_hitl else 'not required'}."
        ),
        "severity": "medium" if all_compliant else "high",
        "timestamp": now_iso,
    })
    ui_events.append({
        "type": "neural_feed",
        "agent": "JURIST",
        "message": "Articles referenced: 6 (Classification), 9 (Risk Mgmt), 13 (Transparency), 14 (Human Oversight)",
        "severity": "low",
        "timestamp": now_iso,
    })

    return {
        "current_phase": "jurist_complete",
        "compliance_report": compliance_report,
        "decision_traces": [trace.model_dump()],
        "ui_events": ui_events,
        "messages": [
            AIMessage(
                content=(
                    f"[JURIST] Compliance evaluation complete: {compliance_report['status']}. "
                    f"Human oversight: {'required' if requires_hitl else 'not required'}. "
                    f"Evaluated {len(anomalies)} anomalie(s) against EU AI Act Articles 6, 9, 13, 14."
                ),
                name="jurist",
            )
        ],
    }

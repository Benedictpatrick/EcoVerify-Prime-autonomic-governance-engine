"""FINALIZE node — submit Jira tickets, settle A2A fees, generate proof-graph.

Responsibilities:
  1. Submit drafted Jira tickets (final state mutation).
  2. Trigger USDC micro-settlement for agent service fees.
  3. Compute fintech risk score for the operation.
  4. Check for edutech friction signals.
  5. Generate a Mermaid.js diagram from decision traces.
  6. Emit completion UI events (proof-graph + execution_complete).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from langchain_core.messages import AIMessage

from ecoverify.agents.state import EcoVerifyState
from ecoverify.telemetry.tracing import agent_span

logger = logging.getLogger(__name__)


def _build_mermaid_graph(decision_traces: list[dict], anomalies: list[dict]) -> str:
    """Build a Mermaid.js flowchart from the decision trace history."""
    lines = [
        "graph TD",
        '    START(("🔄 Start"))',
    ]

    prev_node = "START"
    for i, trace in enumerate(decision_traces):
        agent = trace.get("agent_id", f"agent_{i}")
        decision = trace.get("decision", {})
        action = decision.get("action", "unknown")
        node_id = f"{agent}_{i}"

        # Style based on agent
        shape_open, shape_close = "[", "]"
        if agent == "governor":
            shape_open, shape_close = "{", "}"
        elif agent == "vanguard":
            shape_open, shape_close = "([", "])"

        label = f"{agent.upper()}\\n{action}"
        extra = ""
        if "monthly_savings" in decision:
            extra = f"\\n${decision['monthly_savings']:,.0f}/mo"
        elif "anomalies_found" in decision:
            extra = f"\\n{decision['anomalies_found']} anomalie(s)"
        elif "status" in decision:
            extra = f"\\n{decision['status']}"
        elif "approved" in decision:
            extra = f"\\n{'✅ Approved' if decision['approved'] else '❌ Rejected'}"

        lines.append(f"    {node_id}{shape_open}\"{label}{extra}\"{shape_close}")

        # Edges
        sig_short = trace.get("payload_hash", "")[:8]
        lines.append(f"    {prev_node} -->|\"sig:{sig_short}\"| {node_id}")
        prev_node = node_id

    lines.append(f'    {prev_node} --> END(("✅ Complete"))')

    # Styling
    lines.append("")
    lines.append("    classDef vanguard fill:#1e40af,stroke:#3b82f6,color:#fff")
    lines.append("    classDef jurist fill:#6b21a8,stroke:#a855f7,color:#fff")
    lines.append("    classDef architect fill:#065f46,stroke:#10b981,color:#fff")
    lines.append("    classDef governor fill:#92400e,stroke:#f59e0b,color:#fff")

    for i, trace in enumerate(decision_traces):
        agent = trace.get("agent_id", f"agent_{i}")
        node_id = f"{agent}_{i}"
        if agent in ("vanguard", "jurist", "architect", "governor"):
            lines.append(f"    class {node_id} {agent}")

    return "\n".join(lines)


@agent_span("finalize_node")
def finalize_node(state: EcoVerifyState) -> dict:
    """Final node — submit tickets, build proof-graph, emit completion."""

    now_iso = datetime.now(timezone.utc).isoformat()
    decision_traces = state.get("decision_traces", [])
    anomalies = state.get("anomalies", [])
    simulation = state.get("simulation_result", {})
    jira_tickets = state.get("jira_tickets", [])

    # ── 1. "Submit" Jira tickets (mark as In Progress) ──
    submitted_ids = []
    for ticket in jira_tickets:
        ticket["status"] = "In Progress"
        submitted_ids.append(ticket.get("ticket_id", "unknown"))
    logger.info("Submitted %d Jira tickets: %s", len(submitted_ids), submitted_ids)

    # ── 2. Web3 USDC settlement ─────────────────────────
    settlements: list[dict] = []
    try:
        from ecoverify.web3.models import SettlementRequest
        from ecoverify.web3.settlement import create_settlement

        # Settle service fee: architect → governor (simulated A2A fee)
        fee = round(simulation.get("monthly_savings_usd", 0) * 0.001, 4)  # 0.1% of savings
        if fee > 0:
            receipt = create_settlement(SettlementRequest(
                from_agent="architect",
                to_agent="governor",
                amount_usdc=fee,
                memo=f"A2A service fee for thread execution — {len(anomalies)} anomalies resolved",
            ))
            settlements.append(receipt.model_dump())
    except Exception as e:
        logger.debug("Web3 settlement skipped: %s", e)

    # ── 3. Fintech risk score ───────────────────────────
    risk_scores: list[dict] = []
    try:
        from ecoverify.fintech.risk_scoring import compute_risk_score
        score = compute_risk_score(
            anomalies,
            state.get("compliance_report", {}).get("status", "unknown"),
            simulation.get("monthly_savings_usd", 0),
        )
        risk_scores.append(score.model_dump())
    except Exception as e:
        logger.debug("Risk scoring skipped: %s", e)

    # ── 4. Edutech friction detection ───────────────────
    edutech_hints: list[dict] = []
    try:
        from ecoverify.edutech.friction_detector import detect_friction
        from ecoverify.edutech.upskill_engine import generate_upskill

        error_log = state.get("error_log", [])
        iteration_count = state.get("iteration_count", 0)
        signals = detect_friction(
            self_correction_count=max(iteration_count - 1, 0),
            error_count=len(error_log),
            total_actions=iteration_count,
            agent_phase="finalize",
        )
        if signals:
            recs = generate_upskill(signals)
            for rec in recs:
                edutech_hints.append(rec.model_dump())
    except Exception as e:
        logger.debug("Edutech detection skipped: %s", e)

    # ── 4b. FHIR clinical energy audit ──────────────────
    fhir_observations: list[dict] = []
    fhir_audit_result: dict = {}
    try:
        from ecoverify.health.fhir_client import audit_clinical_energy

        # Use energy readings from telemetry if available
        telemetry = state.get("telemetry_data", {})
        energy_data = telemetry.get("energy", {})
        readings_raw = energy_data.get("readings", [])
        energy_readings = [r.get("kwh", 150.0) if isinstance(r, dict) else float(r) for r in readings_raw[:10]]
        if not energy_readings:
            # Fallback: derive from anomaly peak/avg
            for a in anomalies:
                if a.get("peak_kwh"):
                    energy_readings = [a["avg_kwh"]] * 8 + [a["peak_kwh"]] * 2
                    break
            if not energy_readings:
                energy_readings = [145.0, 138.0, 152.0, 180.0, 141.0]

        facility_id = anomalies[0].get("building_id", "HQ-01") if anomalies else "HQ-01"
        audit = audit_clinical_energy(
            facility_id=facility_id,
            energy_readings=energy_readings,
            facility_type="data_center",
            sqft=60_000.0,
        )
        fhir_audit_result = audit.model_dump()
        fhir_observations = [obs.model_dump() for obs in audit.observations]
        logger.info("FHIR audit: score=%.1f, percentile=%d", audit.energy_efficiency_score, audit.benchmark_percentile)
    except Exception as e:
        logger.debug("FHIR audit skipped: %s", e)

    # ── 4c. Fintech compliance (GENIUS Act + MiCA) ──────
    compliance_results: list[dict] = []
    try:
        from ecoverify.fintech.compliance import check_genius_act, check_mica

        # Check GENIUS Act against settlement data
        settlement_amount = sum(s.get("amount_usdc", 0) for s in settlements)
        agent_ids = list({t.get("agent_id", "") for t in decision_traces if t.get("agent_id")})

        genius = check_genius_act(
            transaction_type="settlement",
            amount_usd=settlement_amount,
            agent_ids=agent_ids,
        )
        compliance_results.append(genius.model_dump())

        # Check MiCA for cross-border EU compliance
        mica = check_mica(
            settlement_type="usdc_transfer",
            amount_eur=settlement_amount * 0.92,  # approx USD→EUR
            cross_border=True,
        )
        compliance_results.append(mica.model_dump())

        logger.info(
            "Fintech compliance: GENIUS=%s, MiCA=%s",
            "PASS" if genius.compliant else "FAIL",
            "PASS" if mica.compliant else "FAIL",
        )
    except Exception as e:
        logger.debug("Fintech compliance skipped: %s", e)

    # ── 5. Generate Mermaid proof-graph ─────────────────
    mermaid_definition = _build_mermaid_graph(decision_traces, anomalies)

    # ── 6. Build execution summary ──────────────────────
    summary = {
        "anomalies_detected": len(anomalies),
        "compliance_status": state.get("compliance_report", {}).get("status", "unknown"),
        "monthly_savings_usd": simulation.get("monthly_savings_usd", 0),
        "npv_3yr_usd": simulation.get("npv_3yr_usd", 0),
        "co2_tons_saved_annual": simulation.get("co2_tons_saved_annual", 0),
        "env_reduction_pct": simulation.get("env_reduction_pct", 0),
        "tickets_submitted": submitted_ids,
        "decision_traces_count": len(decision_traces),
        "governor_approved": state.get("governor_approval", None),
        "fhir_audit_score": fhir_audit_result.get("energy_efficiency_score", None),
        "genius_act_compliant": compliance_results[0].get("compliant") if len(compliance_results) > 0 else None,
        "mica_compliant": compliance_results[1].get("compliant") if len(compliance_results) > 1 else None,
        "completed_at": now_iso,
    }

    # ── 7. UI events ────────────────────────────────────
    ui_events: list[dict] = [
        {
            "type": "proof_graph",
            "mermaid": mermaid_definition,
            "timestamp": now_iso,
        },
        {
            "type": "neural_feed",
            "agent": "SYSTEM",
            "message": (
                f"Loop complete: {len(anomalies)} anomalie(s) resolved, "
                f"${simulation.get('monthly_savings_usd', 0):,.0f}/mo projected saving, "
                f"{len(submitted_ids)} ticket(s) submitted."
            ),
            "severity": "low",
            "timestamp": now_iso,
        },
        {
            "type": "execution_complete",
            "summary": summary,
            "timestamp": now_iso,
        },
    ]

    # Add settlement event
    if settlements:
        ui_events.append({
            "type": "settlement_update",
            "agent": "SYSTEM",
            "message": f"USDC settlement: ${settlements[0].get('amount_usdc', 0):.4f} ({settlements[0].get('status', 'unknown')})",
            "settlement": settlements[0],
            "severity": "low",
            "timestamp": now_iso,
        })
        ui_events.append({
            "type": "neural_feed",
            "agent": "SYSTEM",
            "message": f"💰 A2A settlement: ${settlements[0].get('amount_usdc', 0):.4f} USDC on {settlements[0].get('network', 'devnet')}",
            "severity": "low",
            "timestamp": now_iso,
        })

    # Add risk alert event
    if risk_scores:
        rs = risk_scores[0]
        ui_events.append({
            "type": "risk_alert",
            "agent": "SYSTEM",
            "message": f"Risk score: {rs.get('score', 0):.1f}/100 ({rs.get('category', 'unknown')})",
            "risk_score": rs,
            "severity": "high" if rs.get("score", 0) >= 70 else "medium" if rs.get("score", 0) >= 40 else "low",
            "timestamp": now_iso,
        })
        ui_events.append({
            "type": "neural_feed",
            "agent": "SYSTEM",
            "message": f"📊 Risk Assessment: {rs.get('score', 0):.1f}/100 — {rs.get('recommendation', '')}",
            "severity": "medium" if rs.get("score", 0) >= 40 else "low",
            "timestamp": now_iso,
        })

    # Add edutech hint events
    for hint in edutech_hints:
        ui_events.append({
            "type": "edutech_hint",
            "agent": "SYSTEM",
            "message": f"📚 Upskill: {hint.get('topic', 'Training')}",
            "hint": hint,
            "severity": "low",
            "timestamp": now_iso,
        })

    # Add FHIR audit event
    if fhir_audit_result:
        ui_events.append({
            "type": "fhir_audit",
            "agent": "FHIR",
            "message": (
                f"🏥 FHIR Audit: {fhir_audit_result.get('facility_id', 'N/A')} — "
                f"score {fhir_audit_result.get('energy_efficiency_score', 0)}/100, "
                f"percentile {fhir_audit_result.get('benchmark_percentile', 0)}%"
            ),
            "audit": fhir_audit_result,
            "severity": "medium" if fhir_audit_result.get("energy_efficiency_score", 100) < 60 else "low",
            "timestamp": now_iso,
        })
        ui_events.append({
            "type": "neural_feed",
            "agent": "FHIR",
            "message": (
                f"🏥 Clinical energy audit: "
                f"{fhir_audit_result.get('energy_efficiency_score', 0):.0f}/100 efficiency, "
                f"{len(fhir_audit_result.get('recommendations', []))} recommendation(s)"
            ),
            "severity": "low",
            "timestamp": now_iso,
        })

    # Add fintech compliance events
    for cr in compliance_results:
        status_emoji = "✅" if cr.get("compliant") else "⚠️"
        ui_events.append({
            "type": "neural_feed",
            "agent": "FINTECH",
            "message": f"{status_emoji} {cr.get('framework', 'Unknown')}: {cr.get('details', '')}",
            "severity": "low" if cr.get("compliant") else "high",
            "timestamp": now_iso,
        })

    return {
        "current_phase": "complete",
        "settlements": settlements,
        "risk_scores": risk_scores,
        "edutech_hints": edutech_hints,
        "fhir_observations": fhir_observations,
        "ui_events": ui_events,
        "messages": [
            AIMessage(
                content=(
                    f"[SYSTEM] Execution complete. {len(anomalies)} anomalie(s), "
                    f"${simulation.get('monthly_savings_usd', 0):,.2f}/mo saving, "
                    f"{len(submitted_ids)} ticket(s) submitted, "
                    f"{len(settlements)} settlement(s), risk={risk_scores[0].get('score', 'N/A') if risk_scores else 'N/A'}."
                ),
                name="system",
            )
        ],
    }

"""Demo mode — pre-scripted SSE stream for judges.

Returns a fully choreographed pipeline run with realistic timing,
pre-computed data, and all 9 domain events.  Does NOT touch the real
LangGraph pipeline or any shared state.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/api/demo", tags=["demo"])

# ── Demo data constants ─────────────────────────────────────────────

DEMO_THREAD_ID = f"demo-{uuid.uuid4().hex[:8]}"
BUILDING = "HQ-01"
MONTHLY_SAVINGS = 14_328.72
NPV_3YR = 36_930.41
CO2_ANNUAL = 384.6
ENV_REDUCTION = 30.0
CAMPUS_BUILDINGS = 3
PAYBACK_MONTHS = 1.0


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _demo_events() -> list[tuple[float, dict]]:
    """Return a list of (delay_seconds, event_dict) for the demo."""

    events: list[tuple[float, dict]] = []

    # ── Phase 1: VANGUARD (anomaly detection) ───────────
    events.append((0.0, {
        "type": "phase_change",
        "phase": "starting",
    }))

    events.append((0.8, {
        "type": "neural_feed",
        "agent": "VANGUARD",
        "message": f"BMS telemetry scan initiated for {BUILDING} campus ({CAMPUS_BUILDINGS} buildings)",
        "severity": "low",
        "timestamp": _ts(),
    }))

    events.append((1.5, {
        "type": "neural_feed",
        "agent": "VANGUARD",
        "message": f"⚡ Energy spike detected: +74.4% above baseline in {BUILDING} data center wing",
        "severity": "high",
        "timestamp": _ts(),
    }))

    events.append((0.5, {
        "type": "neural_feed",
        "agent": "VANGUARD",
        "message": f"💧 Water anomaly detected: +62.1% above baseline in cooling system",
        "severity": "medium",
        "timestamp": _ts(),
    }))

    events.append((0.3, {
        "type": "phase_change",
        "phase": "vanguard_complete",
    }))

    # ── Phase 2: JURIST (compliance) ────────────────────
    events.append((1.2, {
        "type": "neural_feed",
        "agent": "JURIST",
        "message": "Evaluating against EU AI Act Article 9 — Risk Management System requirements",
        "severity": "low",
        "timestamp": _ts(),
    }))

    events.append((1.0, {
        "type": "neural_feed",
        "agent": "JURIST",
        "message": "✅ Compliance verified: EU AI Act Art.9 §1-4 satisfied. High-risk AI system monitoring active.",
        "severity": "low",
        "timestamp": _ts(),
    }))

    events.append((0.3, {
        "type": "phase_change",
        "phase": "jurist_complete",
    }))

    # ── Phase 3: ARCHITECT (ROI + 3D) ──────────────────
    events.append((1.5, {
        "type": "neural_feed",
        "agent": "ARCHITECT",
        "message": (
            f"ROI Simulation: +${MONTHLY_SAVINGS:,.0f}/mo across {CAMPUS_BUILDINGS} buildings "
            f"(NPV 3yr: ${NPV_3YR:,.0f}). "
            f"CO₂ reduced: {CO2_ANNUAL:.1f} tons/yr ({ENV_REDUCTION:.0f}%). "
            f"Payback: {PAYBACK_MONTHS} mo."
        ),
        "severity": "low",
        "timestamp": _ts(),
    }))

    # 3D scene data
    import random
    random.seed(42)
    nodes_3d = []
    for row in range(4):
        for col in range(5):
            is_anomaly = (row * 5 + col) % 7 < 2
            nodes_3d.append({
                "id": f"rack-{row}-{col}",
                "position": {"x": (col - 2) * 3.0, "y": 0.0, "z": (row - 1.5) * 3.0},
                "energy_level": round(random.uniform(0.82, 1.0) if is_anomaly else random.uniform(0.3, 0.65), 3),
                "status": "anomaly" if is_anomaly else "normal",
                "color": "#ff3366" if is_anomaly else "#00ff88",
            })
    connections_3d = []
    for row in range(4):
        for col in range(5):
            if col < 4:
                connections_3d.append({"from": f"rack-{row}-{col}", "to": f"rack-{row}-{col + 1}"})
            if row < 3:
                connections_3d.append({"from": f"rack-{row}-{col}", "to": f"rack-{row + 1}-{col}"})

    events.append((0.5, {
        "type": "3d_update",
        "payload": {"nodes": nodes_3d, "connections": connections_3d},
        "timestamp": _ts(),
    }))

    events.append((0.4, {
        "type": "neural_feed",
        "agent": "ARCHITECT",
        "message": "Jira ticket drafted: MAINT-2847 — Energy Spike in HQ-01 data center",
        "severity": "low",
        "timestamp": _ts(),
    }))

    events.append((0.3, {
        "type": "phase_change",
        "phase": "architect_complete",
    }))

    # ── Phase 4: GOVERNOR (HITL interrupt) ──────────────
    events.append((1.0, {
        "type": "governor_panel",
        "action_summary": (
            f"Approve maintenance action for 2 anomalie(s). "
            f"Estimated monthly saving: ${MONTHLY_SAVINGS:,.2f}. "
            f"CO₂ reduction: {CO2_ANNUAL:.1f} tons/yr ({ENV_REDUCTION:.0f}%). "
            f"Compliance status: compliant. Jira tickets to submit: 1."
        ),
        "estimated_roi": MONTHLY_SAVINGS,
        "npv_3yr": NPV_3YR,
        "payback_months": PAYBACK_MONTHS,
        "co2_tons_saved_annual": CO2_ANNUAL,
        "env_reduction_pct": ENV_REDUCTION,
        "campus_buildings": CAMPUS_BUILDINGS,
        "requires_approval": True,
        "timestamp": _ts(),
    }))

    events.append((0.3, {
        "type": "neural_feed",
        "agent": "GOVERNOR",
        "message": "⏳ Awaiting human approval for state-mutating action…",
        "severity": "medium",
        "timestamp": _ts(),
    }))

    events.append((0.2, {
        "type": "interrupt",
        "requires_approval": True,
        "thread_id": "demo",
    }))

    # ── AUTO-APPROVE after 4 seconds (demo mode) ───────
    events.append((4.0, {
        "type": "neural_feed",
        "agent": "GOVERNOR",
        "message": "✅ Action AUTO-APPROVED (demo mode).",
        "severity": "low",
        "timestamp": _ts(),
    }))

    events.append((0.3, {
        "type": "phase_change",
        "phase": "governor_approved",
    }))

    # ── Phase 5: FINALIZE ──────────────────────────────
    events.append((1.5, {
        "type": "neural_feed",
        "agent": "SYSTEM",
        "message": "💰 A2A settlement: $14.3287 USDC on devnet (tx: 5K7x…mQ3)",
        "severity": "low",
        "timestamp": _ts(),
    }))

    events.append((0.3, {
        "type": "settlement_update",
        "agent": "SYSTEM",
        "message": "USDC settlement: $14.3287 (confirmed)",
        "settlement": {
            "tx_signature": "5K7x9vLmN2qR8tW3jF6hY4bC1dA0eZ5K7x9vLmN2qmQ3",
            "from_agent": "architect",
            "to_agent": "governor",
            "amount_usdc": 14.3287,
            "network": "devnet",
            "status": "confirmed",
            "timestamp": _ts(),
            "memo": "A2A service fee — 2 anomalies resolved",
            "block_hash": "0xdemo384f6a2b1c3d5e7f9a0b2c4d6e8f0a2b4c6d8e0f",
        },
        "severity": "low",
        "timestamp": _ts(),
    }))

    events.append((0.8, {
        "type": "neural_feed",
        "agent": "SYSTEM",
        "message": "📊 Risk Assessment: 28.4/100 — Low operational risk. Continue autonomous monitoring.",
        "severity": "low",
        "timestamp": _ts(),
    }))

    events.append((0.3, {
        "type": "risk_alert",
        "agent": "SYSTEM",
        "message": "Risk score: 28.4/100 (low)",
        "risk_score": {
            "score": 28.4,
            "category": "low",
            "severity": "low",
            "source": "finalize",
            "factors": [
                {"name": "anomaly_severity", "score": 35.0, "weight": 0.3},
                {"name": "compliance_gap", "score": 10.0, "weight": 0.25},
                {"name": "financial_exposure", "score": 30.0, "weight": 0.25},
                {"name": "operational_risk", "score": 25.0, "weight": 0.2},
            ],
            "recommendation": "Continue autonomous monitoring. Schedule quarterly review.",
            "timestamp": _ts(),
        },
        "severity": "low",
        "timestamp": _ts(),
    }))

    # FHIR audit
    events.append((0.6, {
        "type": "fhir_audit",
        "agent": "FHIR",
        "message": "🏥 FHIR Audit: HQ-01 — score 72.0/100, percentile 60%",
        "audit": {
            "facility_id": "HQ-01",
            "facility_type": "data_center",
            "energy_efficiency_score": 72.0,
            "benchmark_percentile": 60,
            "recommendations": ["Implement occupancy-based climate control in non-critical areas."],
            "compliance_status": "pass",
        },
        "severity": "low",
        "timestamp": _ts(),
    }))

    events.append((0.3, {
        "type": "neural_feed",
        "agent": "FHIR",
        "message": "🏥 Clinical energy audit: 72/100 efficiency, 1 recommendation(s)",
        "severity": "low",
        "timestamp": _ts(),
    }))

    # Fintech compliance
    events.append((0.5, {
        "type": "neural_feed",
        "agent": "FINTECH",
        "message": "✅ GENIUS_ACT: Transaction type 'settlement' for $14.33 evaluated against 5 GENIUS Act provisions. All checks passed.",
        "severity": "low",
        "timestamp": _ts(),
    }))

    events.append((0.3, {
        "type": "neural_feed",
        "agent": "FINTECH",
        "message": "✅ EU_MICA: Settlement 'usdc_transfer' for €13.18 evaluated against 5 MiCA provisions. All checks passed.",
        "severity": "low",
        "timestamp": _ts(),
    }))

    # Edutech
    events.append((0.4, {
        "type": "edutech_hint",
        "agent": "SYSTEM",
        "message": "📚 Upskill: HVAC Optimization Strategies for Data Centers",
        "hint": {
            "topic": "HVAC Optimization Strategies for Data Centers",
            "urgency": "medium",
            "content": "Learn about advanced cooling strategies to reduce energy consumption in data center environments.",
            "related_articles": ["https://energy.gov/eere/buildings/data-centers"],
            "estimated_minutes": 15,
            "timestamp": _ts(),
        },
        "severity": "low",
        "timestamp": _ts(),
    }))

    # Proof graph
    mermaid = """graph TD
    START(("🔄 Start"))
    vanguard_0(["VANGUARD\\nanomaly_scan\\n2 anomalie(s)"])
    START -->|"sig:a3f7b2c1"| vanguard_0
    jurist_1["JURIST\\ncompliance_evaluation\\ncompliant"]
    vanguard_0 -->|"sig:d4e8f3a2"| jurist_1
    architect_2["ARCHITECT\\nroi_simulation\\n$14,329/mo"]
    jurist_1 -->|"sig:b5c9d4e3"| architect_2
    governor_3{"GOVERNOR\\nhuman_approval\\n✅ Approved"}
    architect_2 -->|"sig:f6a0b5c4"| governor_3
    governor_3 --> END(("✅ Complete"))

    classDef vanguard fill:#1e40af,stroke:#3b82f6,color:#fff
    classDef jurist fill:#6b21a8,stroke:#a855f7,color:#fff
    classDef architect fill:#065f46,stroke:#10b981,color:#fff
    classDef governor fill:#92400e,stroke:#f59e0b,color:#fff
    class vanguard_0 vanguard
    class jurist_1 jurist
    class architect_2 architect
    class governor_3 governor"""

    events.append((0.5, {
        "type": "proof_graph",
        "mermaid": mermaid,
        "timestamp": _ts(),
    }))

    # Completion
    events.append((0.5, {
        "type": "neural_feed",
        "agent": "SYSTEM",
        "message": (
            f"Loop complete: 2 anomalie(s) resolved, "
            f"${MONTHLY_SAVINGS:,.0f}/mo projected saving, "
            f"1 ticket(s) submitted. CO₂ avoided: {CO2_ANNUAL:.0f} t/yr."
        ),
        "severity": "low",
        "timestamp": _ts(),
    }))

    events.append((0.3, {
        "type": "execution_complete",
        "summary": {
            "anomalies_detected": 2,
            "compliance_status": "compliant",
            "monthly_savings_usd": MONTHLY_SAVINGS,
            "npv_3yr_usd": NPV_3YR,
            "co2_tons_saved_annual": CO2_ANNUAL,
            "env_reduction_pct": ENV_REDUCTION,
            "tickets_submitted": ["MAINT-2847"],
            "governor_approved": True,
            "genius_act_compliant": True,
            "mica_compliant": True,
            "fhir_audit_score": 72.0,
            "completed_at": _ts(),
        },
        "timestamp": _ts(),
    }))

    events.append((0.2, {
        "type": "complete",
        "phase": "complete",
    }))

    return events


# ── SSE Endpoint ────────────────────────────────────────────────────

@router.get("/stream")
async def demo_stream():
    """Stream a pre-scripted demo pipeline run via SSE.

    This endpoint is completely isolated from the real LangGraph pipeline.
    """
    events = _demo_events()

    async def generate():
        for delay, event in events:
            if delay > 0:
                await asyncio.sleep(delay)
            yield {
                "event": event.get("type", "update"),
                "data": json.dumps(event),
            }

    return EventSourceResponse(generate())


@router.post("/start")
async def demo_start():
    """Return a demo thread ID so the frontend can connect to the SSE stream."""
    return {
        "thread_id": "demo",
        "status": "demo_started",
        "mode": "demo",
    }


@router.post("/resume")
async def demo_resume():
    """No-op resume for demo mode (auto-approves)."""
    return {
        "thread_id": "demo",
        "status": "demo_resumed",
        "approved": True,
    }

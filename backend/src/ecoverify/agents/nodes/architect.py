"""THE ARCHITECT — What-If ROI analysis and 3D visualisation data.

Responsibilities:
  1. Compute ROI savings for each compliance-cleared anomaly.
  2. Prepare 3D scene data (node positions, energy levels, colours) for the
     React Three Fiber digital twin.
  3. Draft a Jira maintenance ticket via the MCP Jira Ops tool.
  4. Sign simulation with NHI.
  5. Emit UI events: neural feed + 3D scene update.
"""

from __future__ import annotations

import logging
import math
import random
from datetime import datetime, timezone

from langchain_core.messages import AIMessage

from ecoverify.agents.state import EcoVerifyState
from ecoverify.mcp.tools.jira_ops import register_jira_tools
from ecoverify.nhi.keys import load_private_key, generate_agent_keypair
from ecoverify.nhi.signing import sign_decision_trace
from ecoverify.telemetry.tracing import agent_span

logger = logging.getLogger(__name__)

# ── In-process Jira tool access ────────────────────────────────────

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

_jira = _ToolBucket()
register_jira_tools(_jira)


# ── Financial & Environmental parameters ────────────────────────────

COST_PER_KWH = 0.18  # USD — commercial/industrial blended rate
COST_PER_GALLON = 0.008
DISCOUNT_RATE = 0.08  # for NPV
MONTHLY_HOURS = 730
CAMPUS_BUILDINGS = 3  # multi-building campus multiplier
CO2_TONS_PER_KWH = 0.000417  # EPA eGRID US national avg (metric tons CO₂/kWh)
WATER_GALLONS_PER_KWH = 0.5  # cooling water saved per kWh recovered


def _compute_roi(anomalies: list[dict], roi_adjustment: float = 1.0) -> dict:
    """Compute ROI savings + carbon impact from resolving detected anomalies."""

    total_monthly_savings = 0.0
    total_co2_tons_month = 0.0
    total_water_saved_month = 0.0
    details = []

    for a in anomalies:
        if a["type"] == "energy_spike":
            excess_kwh = a.get("peak_kwh", 180) - a.get("avg_kwh", 130)
            recoverable_kwh = excess_kwh * MONTHLY_HOURS * 0.35  # 35% recoverable
            monthly_saving = recoverable_kwh * COST_PER_KWH * CAMPUS_BUILDINGS
            co2_saved = recoverable_kwh * CO2_TONS_PER_KWH * CAMPUS_BUILDINGS
            water_saved = recoverable_kwh * WATER_GALLONS_PER_KWH * CAMPUS_BUILDINGS
        elif a["type"] == "water_spike":
            excess_gal = a.get("peak_gallons", 600) - a.get("avg_gallons", 350)
            monthly_saving = excess_gal * MONTHLY_HOURS * COST_PER_GALLON * 0.30 * CAMPUS_BUILDINGS
            co2_saved = 0.0  # no direct CO₂ from water
            water_saved = excess_gal * MONTHLY_HOURS * 0.30 * CAMPUS_BUILDINGS
        else:
            monthly_saving = 800 * CAMPUS_BUILDINGS  # fallback estimate
            co2_saved = 1.5
            water_saved = 500

        monthly_saving *= roi_adjustment
        total_monthly_savings += monthly_saving
        total_co2_tons_month += co2_saved
        total_water_saved_month += water_saved
        details.append({
            "anomaly_type": a["type"],
            "monthly_saving_usd": round(monthly_saving, 2),
            "co2_tons_saved": round(co2_saved, 3),
        })

    # Environmental 30% reduction projection (annual vs baseline)
    baseline_annual_co2 = total_co2_tons_month * 12 / 0.30 if total_co2_tons_month > 0 else 100
    env_reduction_pct = round((total_co2_tons_month * 12 / max(baseline_annual_co2, 1)) * 100, 1)

    # 3-year NPV
    annual_saving = total_monthly_savings * 12
    npv_3yr = sum(annual_saving / ((1 + DISCOUNT_RATE) ** yr) for yr in range(1, 4))
    payback_months = round(15000 / max(total_monthly_savings, 1), 1)  # $15k campus fix cost

    return {
        "monthly_savings_usd": round(total_monthly_savings, 2),
        "annual_savings_usd": round(annual_saving, 2),
        "npv_3yr_usd": round(npv_3yr, 2),
        "payback_months": payback_months,
        "roi_adjustment": roi_adjustment,
        "co2_tons_saved_monthly": round(total_co2_tons_month, 3),
        "co2_tons_saved_annual": round(total_co2_tons_month * 12, 2),
        "water_gallons_saved_monthly": round(total_water_saved_month, 0),
        "env_reduction_pct": env_reduction_pct,
        "campus_buildings": CAMPUS_BUILDINGS,
        "details": details,
    }


def _generate_3d_scene(anomalies: list[dict]) -> dict:
    """Generate 3D scene data for the digital twin (4×5 rack grid)."""
    nodes = []
    anomaly_buildings = {a.get("building_id", "HQ-01") for a in anomalies}

    for row in range(4):
        for col in range(5):
            node_id = f"rack-{row}-{col}"
            energy_level = random.uniform(0.3, 0.7)
            status = "normal"
            color = "#00ff88"

            # Mark a few racks as anomalous
            if anomalies and (row * 5 + col) % 7 < len(anomalies):
                energy_level = random.uniform(0.8, 1.0)
                status = "anomaly"
                color = "#ff3366"

            nodes.append({
                "id": node_id,
                "position": {
                    "x": (col - 2) * 3.0,
                    "y": 0.0,
                    "z": (row - 1.5) * 3.0,
                },
                "energy_level": round(energy_level, 3),
                "status": status,
                "color": color,
            })

    # Connection lines between adjacent racks
    connections = []
    for row in range(4):
        for col in range(5):
            if col < 4:
                connections.append({
                    "from": f"rack-{row}-{col}",
                    "to": f"rack-{row}-{col + 1}",
                })
            if row < 3:
                connections.append({
                    "from": f"rack-{row}-{col}",
                    "to": f"rack-{row + 1}-{col}",
                })

    return {"nodes": nodes, "connections": connections}


@agent_span("architect_node")
def architect_node(state: EcoVerifyState) -> dict:
    """Simulation node — ROI analysis + 3D visualisation + Jira draft."""

    now_iso = datetime.now(timezone.utc).isoformat()
    anomalies = state.get("anomalies", [])
    roi_adj = 1.0  # may be overridden by Governor feedback

    # Check if Governor sent back an adjustment
    if state.get("governor_approval") is False and state.get("simulation_result"):
        prev = state["simulation_result"]
        roi_adj = prev.get("roi_adjustment", 1.0) * 0.9  # tighten estimate

    # ── 1. ROI computation ──────────────────────────────
    roi = _compute_roi(anomalies, roi_adjustment=roi_adj)

    # ── 2. 3D scene data ────────────────────────────────
    scene = _generate_3d_scene(anomalies)

    # ── 3. Draft Jira ticket ────────────────────────────
    jira_tickets = []
    if anomalies:
        primary = anomalies[0]
        ticket = _jira.create_maintenance_ticket(
            title=f"[Auto] {primary['type'].replace('_', ' ').title()} — {primary.get('building_id', 'HQ-01')}",
            description=(
                f"Anomaly detected: {primary.get('metric', 'N/A')}.\n"
                f"Estimated monthly saving: ${roi['monthly_savings_usd']:,.2f}.\n"
                f"3-year NPV: ${roi['npv_3yr_usd']:,.2f}.\n\n"
                f"Auto-generated by EcoVerify-Prime ARCHITECT agent."
            ),
            priority="High" if primary.get("severity") == "high" else "Medium",
            building_id=primary.get("building_id", "HQ-01"),
        )
        jira_tickets.append(ticket)

    # ── 4. NHI signing ──────────────────────────────────
    try:
        pk = load_private_key("architect")
    except FileNotFoundError:
        pk, _ = generate_agent_keypair("architect")

    trace = sign_decision_trace(
        agent_id="architect",
        decision={
            "action": "roi_simulation",
            "monthly_savings": roi["monthly_savings_usd"],
            "npv_3yr": roi["npv_3yr_usd"],
            "payback_months": roi["payback_months"],
            "co2_tons_saved_annual": roi["co2_tons_saved_annual"],
            "env_reduction_pct": roi["env_reduction_pct"],
            "campus_buildings": CAMPUS_BUILDINGS,
            "tickets_drafted": len(jira_tickets),
        },
        private_key=pk,
    )

    # ── 5. UI events ────────────────────────────────────
    ui_events: list[dict] = [
        {
            "type": "neural_feed",
            "agent": "ARCHITECT",
            "message": (
                f"ROI Simulation: +${roi['monthly_savings_usd']:,.0f}/mo across {CAMPUS_BUILDINGS} buildings "
                f"(NPV 3yr: ${roi['npv_3yr_usd']:,.0f}). "
                f"CO₂ reduced: {roi['co2_tons_saved_annual']:.1f} tons/yr ({roi['env_reduction_pct']}%). "
                f"Payback: {roi['payback_months']} mo."
            ),
            "severity": "low",
            "timestamp": now_iso,
        },
        {
            "type": "3d_update",
            "payload": scene,
            "timestamp": now_iso,
        },
    ]
    if jira_tickets:
        ui_events.append({
            "type": "neural_feed",
            "agent": "ARCHITECT",
            "message": f"Jira ticket drafted: {jira_tickets[0]['ticket_id']}",
            "severity": "low",
            "timestamp": now_iso,
        })

    return {
        "current_phase": "architect_complete",
        "simulation_result": roi,
        "jira_tickets": jira_tickets,
        "decision_traces": [trace.model_dump()],
        "ui_events": ui_events,
        "messages": [
            AIMessage(
                content=(
                    f"[ARCHITECT] ROI simulation complete: ${roi['monthly_savings_usd']:,.2f}/mo, "
                    f"NPV 3yr ${roi['npv_3yr_usd']:,.2f}. "
                    f"{len(jira_tickets)} ticket(s) drafted."
                ),
                name="architect",
            )
        ],
    }

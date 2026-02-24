"""THE VANGUARD — autonomous anomaly detection in BMS telemetry.

Responsibilities:
  1. Fetch energy + water telemetry via MCP tools (simulated in-process).
  2. Detect anomalies (threshold-based + LLM reasoning).
  3. Cite raw data sources before any conclusions (Cite-Before-Act).
  4. Sign findings with NHI Ed25519 key.
  5. Emit UI events for the Neural Feed.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from langchain_core.messages import AIMessage, HumanMessage

from ecoverify.agents.state import EcoVerifyState
from ecoverify.mcp.tools.bms import register_bms_tools
from ecoverify.nhi.keys import load_private_key
from ecoverify.nhi.middleware import cite_data_source
from ecoverify.nhi.signing import sign_decision_trace
from ecoverify.telemetry.tracing import agent_span

logger = logging.getLogger(__name__)

# ── Direct tool access (in-process, no MCP client needed) ──────────

# We create a lightweight namespace to hold the tools registered by
# ``register_bms_tools``.  This avoids standing up a full MCP client
# for the data-plane path while keeping the MCP server available for
# external consumers.

class _ToolBucket:
    """Collects functions registered via ``@mcp.tool()``-style decorator."""
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

_bms = _ToolBucket()
register_bms_tools(_bms)


@agent_span("vanguard_node")
def vanguard_node(state: EcoVerifyState) -> dict:
    """Monitor node — detect anomalies in BMS telemetry."""

    building_id = "HQ-01"
    now_iso = datetime.now(timezone.utc).isoformat()

    # ── 1. Fetch telemetry ──────────────────────────────
    energy = _bms.get_energy_telemetry(building_id=building_id, hours=24)
    water = _bms.get_water_telemetry(building_id=building_id, hours=24)

    # ── 2. Cite data sources (Cite-Before-Act) ──────────
    energy_citation = cite_data_source(
        source_id=f"bms:energy:{building_id}",
        data=energy,
        snippet=f"Energy avg={energy['summary']['avg_kwh']} kWh, peak={energy['summary']['peak_kwh']} kWh",
    )
    water_citation = cite_data_source(
        source_id=f"bms:water:{building_id}",
        data=water,
        snippet=f"Water avg={water['summary']['avg_gallons']} gal, peak={water['summary']['peak_gallons']} gal",
    )

    # ── 3. Detect anomalies ─────────────────────────────
    anomalies: list[dict] = []

    # Energy anomalies
    e_summary = energy["summary"]
    if e_summary["anomaly_count"] > 0:
        pct_above = round(
            ((e_summary["peak_kwh"] - e_summary["avg_kwh"]) / max(e_summary["avg_kwh"], 1)) * 100,
            1,
        )
        anomalies.append({
            "type": "energy_spike",
            "building_id": building_id,
            "severity": "high" if pct_above > 20 else "medium",
            "metric": f"+{pct_above}% above average",
            "peak_kwh": e_summary["peak_kwh"],
            "avg_kwh": e_summary["avg_kwh"],
            "anomaly_count": e_summary["anomaly_count"],
            "detected_at": now_iso,
        })

    # Water anomalies
    w_summary = water["summary"]
    if w_summary["anomaly_count"] > 0:
        pct_above = round(
            ((w_summary["peak_gallons"] - w_summary["avg_gallons"]) / max(w_summary["avg_gallons"], 1)) * 100,
            1,
        )
        anomalies.append({
            "type": "water_spike",
            "building_id": building_id,
            "severity": "high" if pct_above > 25 else "medium",
            "metric": f"+{pct_above}% above average",
            "peak_gallons": w_summary["peak_gallons"],
            "avg_gallons": w_summary["avg_gallons"],
            "anomaly_count": w_summary["anomaly_count"],
            "detected_at": now_iso,
        })

    # ── 4. NHI signing ──────────────────────────────────
    try:
        pk = load_private_key("vanguard")
    except FileNotFoundError:
        from ecoverify.nhi.keys import generate_agent_keypair
        pk, _ = generate_agent_keypair("vanguard")

    trace = sign_decision_trace(
        agent_id="vanguard",
        decision={
            "action": "anomaly_scan",
            "building_id": building_id,
            "anomalies_found": len(anomalies),
            "energy_summary": e_summary,
            "water_summary": w_summary,
        },
        private_key=pk,
    )

    # ── 5. Build UI events ──────────────────────────────
    ui_events: list[dict] = []
    if anomalies:
        primary = anomalies[0]

        # LLM-enhanced anomaly description
        anomaly_message = f"Energy spike detected ({primary['metric']}) in {building_id}"
        try:
            from ecoverify.agents.llm import get_chat_model, is_llm_enabled
            if is_llm_enabled():
                llm = get_chat_model()
                if llm:
                    resp = llm.invoke(
                        f"Summarise this energy anomaly in one professional sentence for a dashboard feed: "
                        f"Building {building_id}, {primary['type']}, {primary['metric']}, "
                        f"severity={primary['severity']}, peak={e_summary['peak_kwh']} kWh, avg={e_summary['avg_kwh']} kWh."
                    )
                    if resp and resp.content:
                        anomaly_message = resp.content.strip()
        except Exception:
            pass  # fall back to deterministic message

        ui_events.append({
            "type": "neural_feed",
            "agent": "VANGUARD",
            "message": anomaly_message,
            "severity": primary["severity"],
            "timestamp": now_iso,
        })
    else:
        ui_events.append({
            "type": "neural_feed",
            "agent": "VANGUARD",
            "message": f"Telemetry nominal for {building_id} — no anomalies detected.",
            "severity": "low",
            "timestamp": now_iso,
        })

    # ── 6. Return state update ──────────────────────────
    return {
        "telemetry_data": {"energy": energy, "water": water},
        "anomalies": anomalies,
        "citations": [energy_citation, water_citation],
        "decision_traces": [trace.model_dump()],
        "current_phase": "vanguard_complete",
        "iteration_count": state.get("iteration_count", 0) + 1,
        "ui_events": ui_events,
        "messages": [
            AIMessage(
                content=(
                    f"[VANGUARD] Scanned {building_id}: "
                    f"{len(anomalies)} anomalie(s) detected. "
                    f"Energy peak={e_summary['peak_kwh']} kWh, "
                    f"Water peak={w_summary['peak_gallons']} gal."
                ),
                name="vanguard",
            )
        ],
    }

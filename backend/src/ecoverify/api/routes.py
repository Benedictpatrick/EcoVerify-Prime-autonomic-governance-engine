"""FastAPI routes — SSE streaming, REST endpoints, and demo triggers.

Endpoints:
  POST /api/run            — start a new graph execution
  GET  /api/stream/{tid}   — SSE stream of UI events
  POST /api/resume/{tid}   — resume after Governor interrupt
  GET  /api/status/{tid}   — current graph state snapshot
  POST /api/inject-anomaly — inject a demo anomaly
  GET  /api/traces/{tid}   — decision trace audit log
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from langgraph.types import Command
from sse_starlette.sse import EventSourceResponse

from ecoverify.agents.graph import get_compiled_graph
from ecoverify.api.schemas import (
    GraphStatusResponse,
    InjectAnomalyRequest,
    PersonalizeRequest,
    PersonalizeResponse,
    ResumeRequest,
    RunRequest,
    SettlementResponse,
)
from ecoverify.mcp.tools.bms import _anomaly_lock, _injected_anomalies

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["ecoverify"])

# ── In-memory run tracking ──────────────────────────────────────────

_active_runs: dict[str, dict] = {}  # thread_id → metadata


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}, "recursion_limit": 25}


# ── POST /api/run ───────────────────────────────────────────────────


@router.post("/run")
async def start_run(req: RunRequest):
    """Start a new EcoVerify graph execution."""
    thread_id = req.thread_id or str(uuid.uuid4())
    graph = get_compiled_graph()

    initial_state = {
        "messages": [],
        "telemetry_data": None,
        "anomalies": [],
        "citations": [],
        "decision_traces": [],
        "compliance_report": None,
        "simulation_result": None,
        "jira_tickets": [],
        "governor_approval": None,
        "settlements": [],
        "risk_scores": [],
        "fhir_observations": [],
        "edutech_hints": [],
        "user_intent": None,
        "current_phase": "starting",
        "error_log": [],
        "iteration_count": 0,
        "ui_events": [],
    }

    _active_runs[thread_id] = {
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "building_id": req.building_id,
    }

    # Run graph in background task
    async def _execute():
        try:
            config = _config(thread_id)
            # Use async stream to process graph events
            async for event in graph.astream(initial_state, config=config, stream_mode="updates"):
                logger.debug("Graph event for %s: %s", thread_id, list(event.keys()))
            _active_runs[thread_id]["status"] = "completed"
        except Exception as exc:
            if "interrupt" in str(type(exc).__name__).lower() or "__interrupt__" in str(exc):
                _active_runs[thread_id]["status"] = "interrupted"
            else:
                _active_runs[thread_id]["status"] = "error"
                _active_runs[thread_id]["error"] = str(exc)
                logger.exception("Graph execution error for %s", thread_id)

    asyncio.create_task(_execute())
    return {"thread_id": thread_id, "status": "started"}


# ── GET /api/stream/{thread_id} ────────────────────────────────────


@router.get("/stream/{thread_id}")
async def stream_events(thread_id: str):
    """SSE endpoint — streams ui_events from the graph state."""
    graph = get_compiled_graph()
    config = _config(thread_id)

    async def event_generator():
        last_event_count = 0
        last_phase = ""
        interrupt_sent = False
        max_polls = 1200  # 5 minutes at 250ms interval
        polls = 0

        while polls < max_polls:
            try:
                state = graph.get_state(config)
                if state and state.values:
                    vals = state.values
                    ui_events = vals.get("ui_events", [])

                    # Send new events since last check
                    new_events = ui_events[last_event_count:]
                    for evt in new_events:
                        yield {
                            "event": evt.get("type", "update"),
                            "data": json.dumps(evt),
                        }
                    last_event_count = len(ui_events)

                    # Emit phase_change whenever it transitions
                    current_phase = vals.get("current_phase", "")
                    if current_phase and current_phase != last_phase:
                        last_phase = current_phase
                        yield {
                            "event": "phase_change",
                            "data": json.dumps({"phase": current_phase}),
                        }

                    # Check if execution is complete
                    if current_phase == "complete":
                        yield {
                            "event": "complete",
                            "data": json.dumps({"phase": current_phase}),
                        }
                        break

                    # Check for interrupt (Governor HITL)
                    tasks = state.tasks if hasattr(state, "tasks") else []
                    has_interrupt = any(
                        hasattr(t, "interrupts") and t.interrupts
                        for t in tasks
                    )
                    if has_interrupt and not interrupt_sent:
                        interrupt_sent = True
                        # Find the interrupt payload and send pre-interrupt events
                        for t in tasks:
                            if hasattr(t, "interrupts") and t.interrupts:
                                for intr in t.interrupts:
                                    interrupt_data = intr.value if hasattr(intr, "value") else {}
                                    if isinstance(interrupt_data, dict):
                                        pre_events = interrupt_data.get("ui_events", [])
                                        for evt in pre_events:
                                            yield {
                                                "event": evt.get("type", "update"),
                                                "data": json.dumps(evt),
                                            }
                                    yield {
                                        "event": "interrupt",
                                        "data": json.dumps({
                                            "type": "governor_interrupt",
                                            "requires_approval": True,
                                            "thread_id": thread_id,
                                        }),
                                    }
                                    break

            except Exception as exc:
                logger.debug("Stream poll error: %s", exc)

            await asyncio.sleep(0.25)
            polls += 1

    return EventSourceResponse(event_generator())


# ── POST /api/resume/{thread_id} ───────────────────────────────────


@router.post("/resume/{thread_id}")
async def resume_run(thread_id: str, req: ResumeRequest):
    """Resume graph execution after Governor HITL interrupt."""
    graph = get_compiled_graph()
    config = _config(thread_id)

    try:
        state = graph.get_state(config)
        if not state or not state.next:
            raise HTTPException(status_code=400, detail="No pending interrupt for this thread.")

        # Resume with human response
        human_response = {
            "approved": req.approved,
            "roi_adjustment": req.roi_adjustment,
        }

        # Run resume in background
        async def _resume():
            try:
                async for event in graph.astream(
                    Command(resume=human_response),
                    config=config,
                    stream_mode="updates",
                ):
                    logger.debug("Resume event for %s: %s", thread_id, list(event.keys()))
                _active_runs.get(thread_id, {})["status"] = "completed"
            except Exception as exc:
                logger.exception("Resume error for %s", thread_id)
                _active_runs.get(thread_id, {})["status"] = "error"

        asyncio.create_task(_resume())
        return {"thread_id": thread_id, "status": "resumed", "approved": req.approved}

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET /api/status/{thread_id} ────────────────────────────────────


@router.get("/status/{thread_id}", response_model=GraphStatusResponse)
async def get_status(thread_id: str):
    """Get current graph state snapshot."""
    graph = get_compiled_graph()
    config = _config(thread_id)

    try:
        state = graph.get_state(config)
        if not state or not state.values:
            return GraphStatusResponse(
                thread_id=thread_id,
                phase="not_found",
            )

        vals = state.values
        run_meta = _active_runs.get(thread_id, {})

        tasks = state.tasks if hasattr(state, "tasks") else []
        has_interrupt = any(
            hasattr(t, "interrupts") and t.interrupts for t in tasks
        )

        return GraphStatusResponse(
            thread_id=thread_id,
            phase=vals.get("current_phase", "unknown"),
            is_running=run_meta.get("status") == "running",
            is_interrupted=has_interrupt,
            anomaly_count=len(vals.get("anomalies", [])),
            compliance_status=vals.get("compliance_report", {}).get("status", "unknown")
            if vals.get("compliance_report")
            else "pending",
            monthly_savings=vals.get("simulation_result", {}).get("monthly_savings_usd", 0)
            if vals.get("simulation_result")
            else 0.0,
            risk_score=vals.get("risk_scores", [{}])[-1].get("score", 0)
            if vals.get("risk_scores")
            else 0.0,
            settlement_count=len(vals.get("settlements", [])),
            fhir_audit_status=vals.get("fhir_observations", [{}])[-1].get("compliance_status", "pending")
            if vals.get("fhir_observations")
            else "pending",
        )
    except Exception:
        return GraphStatusResponse(thread_id=thread_id, phase="error")


# ── POST /api/inject-anomaly ───────────────────────────────────────


@router.post("/inject-anomaly")
async def inject_anomaly(req: InjectAnomalyRequest):
    """Inject a simulated anomaly spike for the live demo.

    Injects both energy and water anomalies for a richer demo experience.
    """
    with _anomaly_lock:
        _injected_anomalies[req.building_id] = req.severity
        _injected_anomalies[f"{req.building_id}:water"] = req.severity * 0.8
    return {
        "status": "injected",
        "building_id": req.building_id,
        "severity": req.severity,
    }


# ── GET /api/traces/{thread_id} ────────────────────────────────────


@router.get("/traces/{thread_id}")
async def get_traces(thread_id: str):
    """Return all decision traces for a thread with verification status."""
    graph = get_compiled_graph()
    config = _config(thread_id)

    try:
        state = graph.get_state(config)
        if not state or not state.values:
            return {"thread_id": thread_id, "traces": []}

        traces = state.values.get("decision_traces", [])

        # Verify each trace with actual NHI public keys
        enriched = []
        for t in traces:
            verified = False
            try:
                from ecoverify.nhi.signing import DecisionTrace, verify_decision_trace
                from ecoverify.nhi.keys import load_public_key
                agent_id = t.get("agent_id", "")
                if agent_id and t.get("signature") and t.get("payload_hash"):
                    pub_key = load_public_key(agent_id)
                    trace_obj = DecisionTrace(**{k: t[k] for k in ("agent_id", "timestamp", "decision", "payload_hash", "signature") if k in t})
                    verified = verify_decision_trace(trace_obj, pub_key)
            except Exception:
                verified = bool(t.get("signature") and t.get("payload_hash"))
            enriched.append({**t, "verified": verified})

        return {"thread_id": thread_id, "traces": enriched, "count": len(enriched)}
    except Exception:
        return {"thread_id": thread_id, "traces": [], "count": 0}


# ── GET /api/settlements/{thread_id} ──────────────────────────────


@router.get("/settlements/{thread_id}", response_model=SettlementResponse)
async def get_settlements(thread_id: str):
    """Return all settlements for a thread."""
    graph = get_compiled_graph()
    config = _config(thread_id)

    try:
        state = graph.get_state(config)
        if not state or not state.values:
            return SettlementResponse(thread_id=thread_id)

        settlements = state.values.get("settlements", [])
        total = sum(s.get("amount_usdc", 0) for s in settlements)
        return SettlementResponse(
            thread_id=thread_id,
            settlements=settlements,
            total_usdc=round(total, 4),
        )
    except Exception:
        return SettlementResponse(thread_id=thread_id)


# ── POST /api/personalize ─────────────────────────────────────────


@router.post("/personalize", response_model=PersonalizeResponse)
async def personalize_dashboard(req: PersonalizeRequest):
    """Return a personalized dashboard config based on interaction telemetry."""
    from ecoverify.media.intent_engine import analyse_intent, generate_dashboard_config
    from ecoverify.media.models import InteractionTelemetry

    telemetry = InteractionTelemetry(
        panel_clicks=req.panel_clicks,
        dwell_times=req.dwell_times,
        approval_latency_s=req.approval_latency_s,
        session_duration_s=req.session_duration_s,
        anomalies_viewed=req.anomalies_viewed,
        proof_graph_expanded=req.proof_graph_expanded,
    )
    intent = analyse_intent(telemetry)
    config = generate_dashboard_config(intent)
    return PersonalizeResponse(
        panel_order=config.panel_order,
        emphasis=config.emphasis,
        detail_level=config.detail_level,
        auto_expand_proof_graph=config.auto_expand_proof_graph,
        highlight_anomalies=config.highlight_anomalies,
        show_settlements=config.show_settlements,
        theme_accent=config.theme_accent,
    )


# ── GET /api/.well-known/agent.json ───────────────────────────────


@router.get("/.well-known/agent.json")
async def get_orchestrator_agent_card():
    """Serve the A2A orchestrator Agent Card."""
    from ecoverify.a2a.discovery import generate_orchestrator_card
    card = generate_orchestrator_card()
    return card.model_dump()


# ── GET /api/a2a/agents ───────────────────────────────────────────


@router.get("/a2a/agents")
async def list_agent_cards():
    """List all agent cards in the swarm."""
    from ecoverify.a2a.discovery import get_all_agent_cards
    cards = get_all_agent_cards()
    return {"agents": [c.model_dump() for c in cards], "count": len(cards)}

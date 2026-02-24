"""EcoVerify-Prime agent state schema.

Defines the ``EcoVerifyState`` TypedDict consumed by LangGraph.  Uses
``Annotated`` reducers so that list-valued fields accumulate across graph
steps rather than being replaced.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from ecoverify.nhi.signing import CitationBlock, DecisionTrace


class EcoVerifyState(TypedDict):
    """Full state for the EcoVerify cyclic graph.

    Fields with ``Annotated[..., operator.add]`` are *additive* — each node
    appends to the existing list rather than replacing it.
    """

    # ── LLM messages ─────────────────────────────────────
    messages: Annotated[list[AnyMessage], add_messages]

    # ── Telemetry ────────────────────────────────────────
    telemetry_data: dict[str, Any] | None
    anomalies: list[dict[str, Any]]

    # ── NHI / Cite-Before-Act ────────────────────────────
    citations: list[CitationBlock]
    decision_traces: Annotated[list[dict], operator.add]

    # ── Compliance ───────────────────────────────────────
    compliance_report: dict[str, Any] | None

    # ── Simulation / ROI ─────────────────────────────────
    simulation_result: dict[str, Any] | None

    # ── Jira ─────────────────────────────────────────────
    jira_tickets: list[dict[str, Any]]

    # ── Governor / HITL ──────────────────────────────────
    governor_approval: bool | None

    # ── Web3 / Settlement ────────────────────────────────
    settlements: Annotated[list[dict[str, Any]], operator.add]

    # ── Fintech / Risk ───────────────────────────────────
    risk_scores: Annotated[list[dict[str, Any]], operator.add]

    # ── Health / FHIR ────────────────────────────────────
    fhir_observations: Annotated[list[dict[str, Any]], operator.add]

    # ── Edutech ──────────────────────────────────────────
    edutech_hints: Annotated[list[dict[str, Any]], operator.add]

    # ── Media Intelligence ───────────────────────────────
    user_intent: dict[str, Any] | None

    # ── Orchestration metadata ───────────────────────────
    current_phase: str
    error_log: Annotated[list[str], operator.add]
    iteration_count: int

    # ── Generative UI events ─────────────────────────────
    ui_events: Annotated[list[dict[str, Any]], operator.add]

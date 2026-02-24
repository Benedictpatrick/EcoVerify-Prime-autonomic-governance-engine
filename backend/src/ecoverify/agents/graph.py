"""LangGraph state machine composition — the EcoVerify cyclic graph.

Assembles the full agent graph:

    START → vanguard → (conditional) → jurist → (conditional) → architect
          → (conditional) → governor → (Command-based) → finalize → END

Self-correction loop:  jurist → vanguard  (on citation failure)
Adjustment loop:       governor → architect  (on ROI rejection)
"""

from __future__ import annotations

import logging
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from ecoverify.agents.edges import (
    route_after_architect,
    route_after_jurist,
    route_after_vanguard,
)
from ecoverify.agents.nodes.architect import architect_node
from ecoverify.agents.nodes.finalize import finalize_node
from ecoverify.agents.nodes.governor import governor_node
from ecoverify.agents.nodes.jurist import jurist_node
from ecoverify.agents.nodes.vanguard import vanguard_node
from ecoverify.agents.state import EcoVerifyState

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    """Construct the EcoVerify state graph (uncompiled)."""
    graph = StateGraph(EcoVerifyState)

    # ── Add nodes ───────────────────────────────────────
    graph.add_node("vanguard", vanguard_node)
    graph.add_node("jurist", jurist_node)
    graph.add_node("architect", architect_node)
    graph.add_node("governor", governor_node)
    graph.add_node("finalize", finalize_node)

    # ── Entry edge ──────────────────────────────────────
    graph.add_edge(START, "vanguard")

    # ── Conditional edges ───────────────────────────────
    graph.add_conditional_edges("vanguard", route_after_vanguard, {
        "jurist": "jurist",
        "__end__": END,
    })

    graph.add_conditional_edges("jurist", route_after_jurist, {
        "vanguard": "vanguard",   # self-correction loop
        "architect": "architect",
        "governor": "governor",   # non-compliant → immediate HITL
        "__end__": END,           # max iterations fallback
    })

    graph.add_conditional_edges("architect", route_after_architect, {
        "governor": "governor",
    })

    # Governor uses Command(goto=...) so we only need the edge to finalize
    # as a named destination reachable via Command
    graph.add_edge("finalize", END)

    return graph


def compile_graph(*, checkpointer=None):
    """Build and compile the graph with a checkpointer.

    Uses ``MemorySaver`` for fast in-process persistence.
    For production, pass a ``PostgresSaver`` or ``SqliteSaver`` (via async
    context manager) for durable persistence.
    """
    if checkpointer is None:
        checkpointer = MemorySaver()

    graph = build_graph()
    compiled = graph.compile(checkpointer=checkpointer)
    logger.info("EcoVerify graph compiled with checkpointer=%s", type(checkpointer).__name__)
    return compiled


# ── Module-level compiled graph (lazy singleton) ────────────────────

_compiled_graph = None


def get_compiled_graph():
    """Return the singleton compiled graph instance."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = compile_graph()
    return _compiled_graph

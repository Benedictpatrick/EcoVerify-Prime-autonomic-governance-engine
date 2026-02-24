"""Agent Card generation and A2A discovery service.

Generates A2A-compliant Agent Cards for the EcoVerify agent swarm and
provides discovery endpoints for external agent interoperability.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ecoverify.a2a.models import AgentCard, TaskAgreement

logger = logging.getLogger(__name__)

# ── Agent Card definitions ──────────────────────────────────────

_AGENT_DEFINITIONS: dict[str, dict] = {
    "vanguard": {
        "name": "The Vanguard",
        "description": "Autonomous anomaly detection agent. Ingests real-time BMS telemetry to detect energy and water anomalies using threshold-based and AI-powered analysis.",
        "capabilities": ["telemetry_ingestion", "anomaly_detection", "data_citation", "nhi_signing"],
    },
    "jurist": {
        "name": "The Jurist",
        "description": "EU AI Act compliance evaluation agent. Performs System 2 reasoning to verify regulatory compliance with high-horizon analysis.",
        "capabilities": ["compliance_evaluation", "regulatory_query", "citation_verification", "risk_classification"],
    },
    "architect": {
        "name": "The Architect",
        "description": "ROI simulation and 3D visualisation agent. Runs What-If scenarios, computes NPV/payback, and generates digital twin scene data.",
        "capabilities": ["roi_analysis", "npv_computation", "3d_scene_generation", "jira_drafting"],
    },
    "governor": {
        "name": "The Governor",
        "description": "Human-in-the-Loop breakpoint agent. Mandatory approval checkpoint for state-mutating actions exceeding configurable thresholds.",
        "capabilities": ["hitl_approval", "roi_adjustment", "action_gating", "threshold_enforcement"],
    },
    "finalize": {
        "name": "The Finalizer",
        "description": "Execution completion agent. Submits Jira tickets, generates Mermaid proof-graphs, and emits completion events.",
        "capabilities": ["ticket_submission", "proof_graph_generation", "settlement_trigger", "audit_trail"],
    },
}


def generate_agent_card(agent_id: str, *, base_url: str = "http://localhost:8000") -> AgentCard:
    """Generate an A2A-compliant Agent Card for a specific agent."""
    defn = _AGENT_DEFINITIONS.get(agent_id)
    if not defn:
        raise ValueError(f"Unknown agent '{agent_id}'. Known agents: {list(_AGENT_DEFINITIONS.keys())}")

    # Try to load NHI public key
    pub_key_b64 = ""
    try:
        from ecoverify.nhi.keys import get_public_key_b64
        pub_key_b64 = get_public_key_b64(agent_id)
    except Exception:
        pass

    return AgentCard(
        agent_id=agent_id,
        name=defn["name"],
        description=defn["description"],
        capabilities=defn["capabilities"],
        protocols=["a2a/1.0", "mcp/1.0", "langgraph/1.0"],
        endpoint=f"{base_url}/api/a2a/agents/{agent_id}",
        public_key_b64=pub_key_b64,
        metadata={
            "framework": "ecoverify-prime",
            "version": "0.1.0",
            "nhi_algorithm": "Ed25519",
        },
    )


def get_all_agent_cards(*, base_url: str = "http://localhost:8000") -> list[AgentCard]:
    """Generate Agent Cards for all known agents."""
    cards = []
    for agent_id in _AGENT_DEFINITIONS:
        try:
            cards.append(generate_agent_card(agent_id, base_url=base_url))
        except Exception as e:
            logger.warning("Failed to generate card for '%s': %s", agent_id, e)
    return cards


def generate_orchestrator_card(*, base_url: str = "http://localhost:8000") -> AgentCard:
    """Generate the top-level orchestrator Agent Card (for .well-known/agent.json)."""
    return AgentCard(
        agent_id="ecoverify-prime",
        name="EcoVerify-Prime Orchestrator",
        description=(
            "Autonomic Global Governor — monitors, verifies, and optimises high-stakes "
            "enterprise operations across environmental, financial, health, and educational "
            "domains using durable LangGraph orchestration."
        ),
        version="0.1.0",
        capabilities=[
            "multi_agent_orchestration",
            "durable_state_machine",
            "nhi_cryptographic_signing",
            "eu_ai_act_compliance",
            "usdc_settlement",
            "fhir_interop",
            "cognitive_friction_detection",
            "intent_aware_ui",
        ],
        protocols=["a2a/1.0", "mcp/1.0", "langgraph/1.0"],
        endpoint=f"{base_url}/api",
        authentication="nhi_ed25519",
        metadata={
            "agents": list(_AGENT_DEFINITIONS.keys()),
            "mcp_endpoint": f"{base_url.replace('8000', '8001')}",
            "documentation": f"{base_url}/docs",
        },
    )


def discover_agents(capability: str) -> list[AgentCard]:
    """Discover agents with a specific capability."""
    all_cards = get_all_agent_cards()
    return [c for c in all_cards if capability in c.capabilities]


def negotiate_task(
    requester_id: str,
    provider_id: str,
    task_description: str,
    fee_usdc: float = 0.0,
) -> TaskAgreement:
    """Create a task agreement between two agents."""
    import uuid
    return TaskAgreement(
        task_id=str(uuid.uuid4()),
        requester_agent=requester_id,
        provider_agent=provider_id,
        task_description=task_description,
        fee_usdc=fee_usdc,
        status="proposed",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

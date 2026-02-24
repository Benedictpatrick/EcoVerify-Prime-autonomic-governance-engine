"""Pydantic models for the A2A protocol."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgentCard(BaseModel):
    """A2A-compliant Agent Card (JSON-LD inspired).

    Based on the Google A2A spec for agent discovery and capability negotiation.
    """

    agent_id: str
    name: str
    description: str
    version: str = "1.0.0"
    capabilities: list[str] = Field(default_factory=list)
    protocols: list[str] = Field(default_factory=lambda: ["a2a/1.0", "mcp/1.0"])
    endpoint: str = ""
    authentication: str = "nhi_ed25519"
    public_key_b64: str = ""
    status: str = "active"  # active | inactive | maintenance
    metadata: dict = Field(default_factory=dict)


class TaskAgreement(BaseModel):
    """Agreement between agents for a specific task."""

    task_id: str
    requester_agent: str
    provider_agent: str
    task_description: str
    estimated_duration_s: float = 0.0
    fee_usdc: float = 0.0
    status: str = "proposed"  # proposed | accepted | rejected | in_progress | completed
    timestamp: str = ""


class A2AMessage(BaseModel):
    """Message exchanged between agents via A2A protocol."""

    from_agent: str
    to_agent: str
    message_type: str  # discover | propose | accept | reject | result | heartbeat
    payload: dict = Field(default_factory=dict)
    timestamp: str = ""
    signature: str = ""  # Ed25519 signature

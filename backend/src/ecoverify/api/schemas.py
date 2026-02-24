"""Pydantic schemas for HTTP request/response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    """Start a new graph execution."""

    thread_id: str = Field(default="", description="If empty, a UUID is generated.")
    trigger: str = Field(default="anomaly_scan", description="Trigger type.")
    building_id: str = Field(default="HQ-01", description="Target building.")


class ResumeRequest(BaseModel):
    """Resume a graph paused at the Governor HITL checkpoint."""

    thread_id: str
    approved: bool = True
    roi_adjustment: float = Field(default=1.0, ge=0.5, le=1.5)


class InjectAnomalyRequest(BaseModel):
    """Inject a simulated anomaly for demo purposes."""

    building_id: str = "HQ-01"
    severity: float = Field(default=0.6, ge=0.0, le=1.0)


class GraphStatusResponse(BaseModel):
    """Snapshot of current graph state."""

    thread_id: str
    phase: str
    is_running: bool = False
    is_interrupted: bool = False
    anomaly_count: int = 0
    compliance_status: str = "unknown"
    monthly_savings: float = 0.0
    risk_score: float = 0.0
    settlement_count: int = 0
    fhir_audit_status: str = "pending"


class SSEEvent(BaseModel):
    """Typed wrapper for Server-Sent Events."""

    type: str
    payload: dict = Field(default_factory=dict)
    timestamp: str = ""


class PersonalizeRequest(BaseModel):
    """Interaction telemetry for dashboard personalization."""

    panel_clicks: dict[str, int] = Field(default_factory=dict)
    dwell_times: dict[str, float] = Field(default_factory=dict)
    approval_latency_s: float = 0.0
    session_duration_s: float = 0.0
    anomalies_viewed: int = 0
    proof_graph_expanded: bool = False


class PersonalizeResponse(BaseModel):
    """Personalized dashboard configuration."""

    panel_order: list[str] = Field(default_factory=list)
    emphasis: str = "balanced"
    detail_level: str = "standard"
    auto_expand_proof_graph: bool = False
    highlight_anomalies: bool = True
    show_settlements: bool = True
    theme_accent: str = "#00ff88"


class SettlementResponse(BaseModel):
    """Settlement query response."""

    thread_id: str
    settlements: list[dict] = Field(default_factory=list)
    total_usdc: float = 0.0

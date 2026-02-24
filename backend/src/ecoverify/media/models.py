"""Pydantic models for the Media Intelligence domain."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UserIntent(BaseModel):
    """Inferred user intent from interaction telemetry."""

    primary_focus: str = "overview"  # overview | compliance | energy | financial | technical
    detail_level: str = "standard"  # minimal | standard | detailed | expert
    urgency: str = "normal"  # low | normal | high | critical
    preferred_panels: list[str] = Field(default_factory=lambda: ["digital_twin", "neural_feed", "metrics"])
    timestamp: str = ""


class DashboardConfig(BaseModel):
    """Personalized dashboard configuration."""

    panel_order: list[str] = Field(default_factory=lambda: [
        "metrics", "digital_twin", "neural_feed", "volume_chart",
        "recent_events", "transactions", "proof_graph",
    ])
    emphasis: str = "balanced"  # compliance | energy | financial | balanced
    detail_level: str = "standard"
    auto_expand_proof_graph: bool = False
    highlight_anomalies: bool = True
    show_settlements: bool = True
    theme_accent: str = "#00ff88"  # adaptive accent colour


class PersonalizationProfile(BaseModel):
    """Operator personalisation profile built from interaction history."""

    operator_id: str = "default"
    role: str = "operator"  # operator | executive | auditor | engineer
    total_sessions: int = 0
    avg_approval_time_s: float = 30.0
    preferred_detail: str = "standard"
    interaction_history: list[dict] = Field(default_factory=list)
    dashboard_config: DashboardConfig = Field(default_factory=DashboardConfig)


class InteractionTelemetry(BaseModel):
    """Telemetry payload from frontend interaction tracking."""

    panel_clicks: dict[str, int] = Field(default_factory=dict)  # panel_name → click_count
    dwell_times: dict[str, float] = Field(default_factory=dict)  # panel_name → seconds
    approval_latency_s: float = 0.0
    session_duration_s: float = 0.0
    anomalies_viewed: int = 0
    proof_graph_expanded: bool = False

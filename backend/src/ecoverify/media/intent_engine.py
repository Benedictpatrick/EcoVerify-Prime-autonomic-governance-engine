"""Intent engine — analyses user interaction patterns to infer dashboard intent.

Determines which panels to emphasize, what detail level to present, and
whether to adapt the layout based on operator behaviour patterns.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ecoverify.media.models import DashboardConfig, InteractionTelemetry, UserIntent

logger = logging.getLogger(__name__)


def analyse_intent(telemetry: InteractionTelemetry) -> UserIntent:
    """Infer user intent from interaction telemetry."""
    now_iso = datetime.now(timezone.utc).isoformat()

    # Determine primary focus based on panel dwell times
    dwell = telemetry.dwell_times
    if dwell:
        top_panel = max(dwell, key=dwell.get)
        focus_map = {
            "digital_twin": "energy",
            "neural_feed": "technical",
            "metrics": "financial",
            "proof_graph": "compliance",
            "transactions": "financial",
            "governor_panel": "compliance",
        }
        primary_focus = focus_map.get(top_panel, "overview")
    else:
        primary_focus = "overview"

    # Determine detail level from session behaviour
    total_clicks = sum(telemetry.panel_clicks.values())
    if total_clicks > 20:
        detail_level = "expert"
    elif total_clicks > 10:
        detail_level = "detailed"
    elif total_clicks > 3:
        detail_level = "standard"
    else:
        detail_level = "minimal"

    # Determine urgency
    if telemetry.anomalies_viewed > 3 or telemetry.approval_latency_s > 120:
        urgency = "high"
    elif telemetry.anomalies_viewed > 1:
        urgency = "normal"
    else:
        urgency = "low"

    # Preferred panels based on click patterns
    preferred = sorted(
        telemetry.panel_clicks.keys(),
        key=lambda p: telemetry.panel_clicks.get(p, 0),
        reverse=True,
    )[:5] if telemetry.panel_clicks else ["digital_twin", "neural_feed", "metrics"]

    return UserIntent(
        primary_focus=primary_focus,
        detail_level=detail_level,
        urgency=urgency,
        preferred_panels=preferred,
        timestamp=now_iso,
    )


def generate_dashboard_config(intent: UserIntent) -> DashboardConfig:
    """Generate a personalised dashboard configuration from inferred intent."""

    # Base panel order
    emphasis = intent.primary_focus if intent.primary_focus != "overview" else "balanced"

    # Reorder panels based on focus
    panel_priority = {
        "compliance": ["proof_graph", "neural_feed", "metrics", "digital_twin", "transactions", "volume_chart", "recent_events"],
        "energy": ["digital_twin", "metrics", "neural_feed", "volume_chart", "recent_events", "proof_graph", "transactions"],
        "financial": ["metrics", "transactions", "volume_chart", "digital_twin", "neural_feed", "recent_events", "proof_graph"],
        "technical": ["neural_feed", "digital_twin", "proof_graph", "metrics", "volume_chart", "recent_events", "transactions"],
        "balanced": ["metrics", "digital_twin", "neural_feed", "volume_chart", "recent_events", "transactions", "proof_graph"],
    }

    panel_order = panel_priority.get(emphasis, panel_priority["balanced"])

    # Accent colours by focus
    accent_map = {
        "compliance": "#a855f7",  # purple
        "energy": "#00ff88",  # green
        "financial": "#f59e0b",  # amber
        "technical": "#3b82f6",  # blue
        "balanced": "#00ff88",
    }

    return DashboardConfig(
        panel_order=panel_order,
        emphasis=emphasis,
        detail_level=intent.detail_level,
        auto_expand_proof_graph=emphasis == "compliance",
        highlight_anomalies=intent.urgency in ("high", "critical"),
        show_settlements=emphasis in ("financial", "balanced"),
        theme_accent=accent_map.get(emphasis, "#00ff88"),
    )

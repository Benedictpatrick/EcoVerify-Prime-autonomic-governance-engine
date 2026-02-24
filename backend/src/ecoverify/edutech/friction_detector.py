"""Cognitive friction detector — monitors interaction patterns for learning signals.

Analyses approval latency, rejection patterns, self-correction frequency, and
error rates to identify moments of operator confusion or skill gaps.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ecoverify.edutech.models import FrictionSignal

logger = logging.getLogger(__name__)

# ── Thresholds ──────────────────────────────────────────────────

SLOW_APPROVAL_THRESHOLD_S = 60.0  # seconds
MAX_SELF_CORRECTIONS = 3
HIGH_ERROR_RATE = 0.3


def detect_friction(
    approval_latency_s: float = 0.0,
    rejection_count: int = 0,
    self_correction_count: int = 0,
    error_count: int = 0,
    total_actions: int = 1,
    agent_phase: str = "",
) -> list[FrictionSignal]:
    """Detect cognitive friction signals from interaction metrics.

    Returns a list of ``FrictionSignal`` instances (may be empty).
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    signals: list[FrictionSignal] = []

    if approval_latency_s > SLOW_APPROVAL_THRESHOLD_S:
        signals.append(FrictionSignal(
            signal_type="slow_approval",
            severity="medium" if approval_latency_s < 120 else "high",
            context=f"Approval took {approval_latency_s:.0f}s (threshold: {SLOW_APPROVAL_THRESHOLD_S:.0f}s)",
            agent_phase=agent_phase,
            duration_seconds=approval_latency_s,
            timestamp=now_iso,
        ))

    if rejection_count >= 2:
        signals.append(FrictionSignal(
            signal_type="repeated_rejection",
            severity="high" if rejection_count >= 3 else "medium",
            context=f"Operator rejected {rejection_count} consecutive actions",
            agent_phase=agent_phase,
            timestamp=now_iso,
        ))

    if self_correction_count >= MAX_SELF_CORRECTIONS:
        signals.append(FrictionSignal(
            signal_type="self_correction_loop",
            severity="high",
            context=f"Agent self-corrected {self_correction_count} times (limit: {MAX_SELF_CORRECTIONS})",
            agent_phase=agent_phase,
            timestamp=now_iso,
        ))

    error_rate = error_count / max(total_actions, 1)
    if error_rate >= HIGH_ERROR_RATE and error_count >= 2:
        signals.append(FrictionSignal(
            signal_type="high_error_rate",
            severity="high" if error_rate >= 0.5 else "medium",
            context=f"Error rate {error_rate:.0%} ({error_count}/{total_actions} actions)",
            agent_phase=agent_phase,
            timestamp=now_iso,
        ))

    if signals:
        logger.info("Detected %d cognitive friction signal(s) in phase '%s'", len(signals), agent_phase)
    return signals

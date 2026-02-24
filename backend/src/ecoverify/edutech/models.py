"""Pydantic models for the Edutech domain."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FrictionSignal(BaseModel):
    """Detected cognitive friction in operator interaction."""

    signal_type: str  # slow_approval | repeated_rejection | self_correction_loop | high_error_rate
    severity: str = "medium"  # low | medium | high
    context: str = ""  # what triggered the friction
    agent_phase: str = ""  # which agent phase it occurred in
    duration_seconds: float = 0.0
    timestamp: str = ""


class UpskillRecommendation(BaseModel):
    """Just-in-time training recommendation for operators."""

    topic: str
    urgency: str = "suggested"  # suggested | recommended | required
    content: str = ""  # the actual micro-lesson or guidance
    related_articles: list[str] = Field(default_factory=list)
    estimated_minutes: int = 5
    timestamp: str = ""


class LearningPath(BaseModel):
    """Aggregated learning path for an operator."""

    operator_id: str = "default"
    recommendations: list[UpskillRecommendation] = Field(default_factory=list)
    friction_history: list[FrictionSignal] = Field(default_factory=list)
    skill_gaps: list[str] = Field(default_factory=list)

"""Pydantic models for the Fintech risk-scoring domain."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RiskScore(BaseModel):
    """Composite risk score for an operational decision."""

    score: float = Field(ge=0.0, le=100.0, description="0=no risk, 100=critical")
    category: str = "operational"  # operational | financial | compliance | reputational
    factors: list[dict] = Field(default_factory=list)
    recommendation: str = ""
    timestamp: str = ""


class ComplianceResult(BaseModel):
    """Result of a regulatory compliance check."""

    framework: str  # "GENIUS_ACT" | "EU_MICA" | "EU_AI_ACT"
    compliant: bool
    violations: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.9)
    details: str = ""
    timestamp: str = ""


class FinancialExposure(BaseModel):
    """Aggregated financial exposure from detected anomalies."""

    total_monthly_cost: float = 0.0
    total_annual_cost: float = 0.0
    potential_savings: float = 0.0
    risk_adjusted_savings: float = 0.0
    currency: str = "USD"

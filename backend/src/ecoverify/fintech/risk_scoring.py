"""Autonomous risk scoring engine.

Computes composite risk scores from anomaly severity, compliance status,
and financial exposure.  Scores against configurable thresholds.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone

from ecoverify.fintech.models import FinancialExposure, RiskScore

logger = logging.getLogger(__name__)

# ── Risk weight matrix ──────────────────────────────────────────

SEVERITY_WEIGHTS = {"high": 0.9, "medium": 0.5, "low": 0.2}
COMPLIANCE_PENALTY = {"non_compliant": 30.0, "compliant": 0.0, "unknown": 15.0}


def compute_risk_score(
    anomalies: list[dict],
    compliance_status: str = "unknown",
    financial_exposure: float = 0.0,
) -> RiskScore:
    """Compute a composite risk score from operational data.

    The score blends anomaly severity, compliance posture, and financial
    exposure into a 0–100 scale.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    factors = []

    # Factor 1: Anomaly severity aggregate
    severity_score = 0.0
    for a in anomalies:
        w = SEVERITY_WEIGHTS.get(a.get("severity", "medium"), 0.5)
        severity_score += w * 25  # each high anomaly contributes ~22.5
    severity_score = min(severity_score, 50.0)
    factors.append({"name": "anomaly_severity", "score": round(severity_score, 1), "weight": 0.4})

    # Factor 2: Compliance posture
    comp_score = COMPLIANCE_PENALTY.get(compliance_status, 15.0)
    factors.append({"name": "compliance_posture", "score": round(comp_score, 1), "weight": 0.35})

    # Factor 3: Financial exposure (logarithmic scaling)
    fin_score = min(math.log1p(financial_exposure / 1000) * 10, 20.0)
    factors.append({"name": "financial_exposure", "score": round(fin_score, 1), "weight": 0.25})

    # Weighted composite
    composite = (
        severity_score * 0.4
        + comp_score * 0.35
        + fin_score * 0.25
    )
    composite = min(round(composite, 1), 100.0)

    # Risk category
    if composite >= 70:
        category = "critical"
    elif composite >= 40:
        category = "elevated"
    else:
        category = "nominal"

    recommendation = _generate_recommendation(composite, anomalies, compliance_status)

    return RiskScore(
        score=composite,
        category=category,
        factors=factors,
        recommendation=recommendation,
        timestamp=now_iso,
    )


def _generate_recommendation(score: float, anomalies: list[dict], compliance: str) -> str:
    if score >= 70:
        return (
            f"CRITICAL: Immediate action required. {len(anomalies)} anomalie(s) detected "
            f"with {compliance} compliance status. Activate incident response protocol."
        )
    elif score >= 40:
        return (
            f"ELEVATED: Monitoring escalated. {len(anomalies)} anomalie(s) under review. "
            "Schedule maintenance within 48 hours."
        )
    return "NOMINAL: All metrics within acceptable thresholds. Continue standard monitoring."


def compute_financial_exposure(anomalies: list[dict], roi_data: dict | None = None) -> FinancialExposure:
    """Aggregate financial exposure from anomalies and ROI data."""
    monthly_cost = 0.0
    for a in anomalies:
        if a.get("type") == "energy_spike":
            excess = a.get("peak_kwh", 180) - a.get("avg_kwh", 130)
            monthly_cost += excess * 730 * 0.12
        elif a.get("type") == "water_spike":
            excess = a.get("peak_gallons", 600) - a.get("avg_gallons", 350)
            monthly_cost += excess * 730 * 0.005

    potential_savings = roi_data.get("monthly_savings_usd", 0) if roi_data else monthly_cost * 0.3
    risk_adjusted = potential_savings * 0.85  # 15% risk haircut

    return FinancialExposure(
        total_monthly_cost=round(monthly_cost, 2),
        total_annual_cost=round(monthly_cost * 12, 2),
        potential_savings=round(potential_savings, 2),
        risk_adjusted_savings=round(risk_adjusted, 2),
    )

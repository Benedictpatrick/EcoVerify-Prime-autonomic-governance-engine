"""Pydantic models for the Health / FHIR domain."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FHIRObservation(BaseModel):
    """Simplified FHIR R4 Observation resource for energy auditing."""

    resource_type: str = "Observation"
    id: str = ""
    status: str = "final"  # registered | preliminary | final | amended
    category: str = "survey"  # survey for environment observation
    code: str = "energy-efficiency"
    value_quantity: float = 0.0
    unit: str = "kWh"
    effective_date_time: str = ""
    subject_reference: str = ""  # Patient/Location reference
    performer_reference: str = "Practitioner/ecoverify-prime"


class ClinicalEnergyAudit(BaseModel):
    """Results of auditing energy efficiency in a clinical environment."""

    facility_id: str
    facility_type: str = "hospital"
    energy_efficiency_score: float = Field(ge=0.0, le=100.0, default=75.0)
    benchmark_percentile: int = Field(ge=0, le=100, default=50)
    observations: list[FHIRObservation] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    compliance_status: str = "compliant"
    timestamp: str = ""


class FacilityBenchmark(BaseModel):
    """Energy benchmark for a facility type."""

    facility_type: str
    avg_kwh_per_sqft: float
    target_kwh_per_sqft: float
    top_quartile_kwh: float

"""HL7 FHIR R4 client for clinical environment energy auditing.

Uses the public HAPI FHIR test server for development/demo.  In production,
this would connect to an institutional FHIR endpoint with OAuth2.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

import httpx

from ecoverify.config import settings
from ecoverify.health.models import ClinicalEnergyAudit, FacilityBenchmark, FHIRObservation

logger = logging.getLogger(__name__)

# ── Facility benchmarks (EnergyStar-aligned) ────────────────────

BENCHMARKS: dict[str, FacilityBenchmark] = {
    "hospital": FacilityBenchmark(
        facility_type="hospital",
        avg_kwh_per_sqft=26.0,
        target_kwh_per_sqft=21.0,
        top_quartile_kwh=18.0,
    ),
    "clinic": FacilityBenchmark(
        facility_type="clinic",
        avg_kwh_per_sqft=18.0,
        target_kwh_per_sqft=14.0,
        top_quartile_kwh=11.0,
    ),
    "data_center": FacilityBenchmark(
        facility_type="data_center",
        avg_kwh_per_sqft=100.0,
        target_kwh_per_sqft=75.0,
        top_quartile_kwh=60.0,
    ),
}


def get_benchmark(facility_type: str) -> FacilityBenchmark:
    """Return energy benchmark for a facility type."""
    return BENCHMARKS.get(facility_type, BENCHMARKS["hospital"])


async def create_fhir_observation(
    facility_id: str,
    energy_kwh: float,
    *,
    facility_type: str = "hospital",
) -> FHIRObservation:
    """Create an Observation resource on the FHIR server (or simulate).

    In demo mode, creates a local observation without calling the remote server
    to avoid network dependency.
    """
    obs = FHIRObservation(
        id=str(uuid.uuid4()),
        status="final",
        code="energy-efficiency",
        value_quantity=energy_kwh,
        unit="kWh",
        effective_date_time=datetime.now(timezone.utc).isoformat(),
        subject_reference=f"Location/{facility_id}",
    )

    # Attempt to POST to FHIR server (non-blocking, best-effort)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{settings.fhir_base_url}/Observation",
                json={
                    "resourceType": "Observation",
                    "id": obs.id,
                    "status": obs.status,
                    "code": {"coding": [{"system": "http://ecoverify.io/codes", "code": obs.code}]},
                    "valueQuantity": {"value": obs.value_quantity, "unit": obs.unit},
                    "effectiveDateTime": obs.effective_date_time,
                    "subject": {"reference": obs.subject_reference},
                },
            )
            if resp.status_code in (200, 201):
                logger.info("FHIR Observation created: %s", obs.id)
            else:
                logger.warning("FHIR POST returned %d: %s", resp.status_code, resp.text[:200])
    except Exception as e:
        logger.debug("FHIR server unavailable (demo mode OK): %s", e)

    return obs


def audit_clinical_energy(
    facility_id: str,
    energy_readings: list[float],
    *,
    facility_type: str = "hospital",
    sqft: float = 50_000.0,
) -> ClinicalEnergyAudit:
    """Audit energy efficiency of a clinical facility synchronously.

    Compares per-sqft energy consumption to EnergyStar-aligned benchmarks.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    benchmark = get_benchmark(facility_type)

    avg_kwh = sum(energy_readings) / max(len(energy_readings), 1)
    kwh_per_sqft = avg_kwh / max(sqft, 1) * 8760  # annualise from hourly readings

    # Score: 100 = top quartile, 0 = 2× above average
    if kwh_per_sqft <= benchmark.top_quartile_kwh:
        score = 95.0
        percentile = 90
    elif kwh_per_sqft <= benchmark.target_kwh_per_sqft:
        score = 75.0
        percentile = 60
    elif kwh_per_sqft <= benchmark.avg_kwh_per_sqft:
        score = 50.0
        percentile = 40
    else:
        ratio = kwh_per_sqft / benchmark.avg_kwh_per_sqft
        score = max(100 - ratio * 50, 5.0)
        percentile = max(100 - int(ratio * 40), 5)

    recommendations = []
    if score < 50:
        recommendations.append("Schedule HVAC efficiency review within 30 days.")
        recommendations.append("Consider LED lighting retrofit for surgical suites.")
    if score < 75:
        recommendations.append("Implement occupancy-based climate control in non-critical areas.")

    # Create observations for each reading
    observations = []
    for reading in energy_readings[:5]:  # cap at 5 for demo
        observations.append(FHIRObservation(
            id=str(uuid.uuid4()),
            value_quantity=reading,
            effective_date_time=now_iso,
            subject_reference=f"Location/{facility_id}",
        ))

    return ClinicalEnergyAudit(
        facility_id=facility_id,
        facility_type=facility_type,
        energy_efficiency_score=round(score, 1),
        benchmark_percentile=percentile,
        observations=observations,
        recommendations=recommendations,
        compliance_status="compliant" if score >= 50 else "review_required",
        timestamp=now_iso,
    )

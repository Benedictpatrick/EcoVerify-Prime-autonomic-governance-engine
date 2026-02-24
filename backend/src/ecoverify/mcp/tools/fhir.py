"""MCP tool registration — Health / FHIR clinical energy auditing."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def register_fhir_tools(server) -> None:
    """Register FHIR/health audit tools on *server*."""

    @server.tool()
    def audit_clinical_energy(
        facility_id: str = "CLINIC-01",
        facility_type: str = "hospital",
        energy_readings_csv: str = "150.0,162.5,145.3,170.2,155.8",
        sqft: float = 50000.0,
    ) -> dict:
        """Audit energy efficiency of a clinical facility against EnergyStar benchmarks.

        Parameters
        ----------
        facility_id : str
            Identifier for the clinical facility.
        facility_type : str
            Type of facility (hospital, clinic, data_center).
        energy_readings_csv : str
            Comma-separated hourly kWh readings.
        sqft : float
            Facility square footage.
        """
        from ecoverify.health.fhir_client import audit_clinical_energy as _audit

        readings = [float(x.strip()) for x in energy_readings_csv.split(",") if x.strip()]
        result = _audit(facility_id, readings, facility_type=facility_type, sqft=sqft)
        return result.model_dump()

    @server.tool()
    def get_facility_benchmark(facility_type: str = "hospital") -> dict:
        """Get EnergyStar-aligned energy benchmark for a facility type.

        Parameters
        ----------
        facility_type : str
            Type of facility (hospital, clinic, data_center).
        """
        from ecoverify.health.fhir_client import get_benchmark

        benchmark = get_benchmark(facility_type)
        return benchmark.model_dump()

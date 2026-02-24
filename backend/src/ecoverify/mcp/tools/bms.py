"""BMS (Building Management System) MCP tools.

Exposes simulated IoT telemetry for energy and water consumption with
realistic patterns: sinusoidal day/night baseline + random noise + optional
injected anomaly spikes for demo purposes.
"""

from __future__ import annotations

import math
import random
import threading
from datetime import datetime, timedelta, timezone

# ── Shared state for anomaly injection ──────────────────────────────

_anomaly_lock = threading.Lock()
_injected_anomalies: dict[str, float] = {}  # building_id → severity


def register_bms_tools(mcp):
    """Register BMS tools on the given FastMCP server instance."""

    @mcp.tool()
    def get_energy_telemetry(building_id: str, hours: int = 24) -> dict:
        """Fetch simulated energy telemetry for a building.

        Returns hourly kWh readings with anomaly scores.
        """
        now = datetime.now(timezone.utc)
        readings = []
        anomaly_count = 0
        total_kwh = 0.0

        # Check for injected anomaly
        with _anomaly_lock:
            injected_severity = _injected_anomalies.pop(building_id, 0.0)

        for i in range(hours):
            ts = now - timedelta(hours=hours - 1 - i)
            hour_of_day = ts.hour

            # Sinusoidal baseline: peaks at 14:00 (~180 kWh), troughs at 03:00 (~80 kWh)
            baseline = 130 + 50 * math.sin((hour_of_day - 3) * math.pi / 12)
            noise = random.gauss(0, 8)
            kwh = max(0, baseline + noise)

            # Inject anomaly spike in the last 3 hours
            anomaly_score = 0.0
            if injected_severity > 0 and i >= hours - 3:
                spike = baseline * injected_severity * random.uniform(0.8, 1.2)
                kwh += spike
                anomaly_score = min(1.0, 0.5 + injected_severity * 0.4)
            elif kwh > baseline * 1.15:
                anomaly_score = min(1.0, (kwh - baseline) / baseline)

            if anomaly_score > 0.3:
                anomaly_count += 1

            total_kwh += kwh
            readings.append({
                "timestamp": ts.isoformat(),
                "kwh": round(kwh, 2),
                "anomaly_score": round(anomaly_score, 3),
            })

        avg_kwh = total_kwh / max(len(readings), 1)
        peak_kwh = max(r["kwh"] for r in readings)

        return {
            "building_id": building_id,
            "readings": readings,
            "summary": {
                "avg_kwh": round(avg_kwh, 2),
                "peak_kwh": round(peak_kwh, 2),
                "anomaly_count": anomaly_count,
                "total_kwh": round(total_kwh, 2),
                "hours_sampled": hours,
            },
        }

    @mcp.tool()
    def get_water_telemetry(building_id: str, hours: int = 24) -> dict:
        """Fetch simulated water consumption telemetry for a building.

        Returns hourly gallon readings with anomaly scores.
        """
        now = datetime.now(timezone.utc)
        readings = []
        anomaly_count = 0
        total_gallons = 0.0

        with _anomaly_lock:
            injected_severity = _injected_anomalies.pop(f"{building_id}:water", 0.0)

        for i in range(hours):
            ts = now - timedelta(hours=hours - 1 - i)
            hour_of_day = ts.hour

            # Water usage: peaks during business hours (09:00-17:00)
            if 8 <= hour_of_day <= 18:
                baseline = 450 + 100 * math.sin((hour_of_day - 8) * math.pi / 10)
            else:
                baseline = 120 + random.gauss(0, 15)

            noise = random.gauss(0, 20)
            gallons = max(0, baseline + noise)

            anomaly_score = 0.0
            if injected_severity > 0 and i >= hours - 3:
                spike = baseline * injected_severity * random.uniform(0.7, 1.3)
                gallons += spike
                anomaly_score = min(1.0, 0.4 + injected_severity * 0.5)
            elif gallons > baseline * 1.2:
                anomaly_score = min(1.0, (gallons - baseline) / baseline)

            if anomaly_score > 0.3:
                anomaly_count += 1

            total_gallons += gallons
            readings.append({
                "timestamp": ts.isoformat(),
                "gallons": round(gallons, 2),
                "anomaly_score": round(anomaly_score, 3),
            })

        avg_gallons = total_gallons / max(len(readings), 1)
        peak_gallons = max(r["gallons"] for r in readings)

        return {
            "building_id": building_id,
            "readings": readings,
            "summary": {
                "avg_gallons": round(avg_gallons, 2),
                "peak_gallons": round(peak_gallons, 2),
                "anomaly_count": anomaly_count,
                "total_gallons": round(total_gallons, 2),
                "hours_sampled": hours,
            },
        }

    @mcp.tool()
    def inject_anomaly(building_id: str, severity: float = 0.5) -> dict:
        """Inject a simulated energy anomaly spike for demo purposes.

        Severity ranges from 0.0 (no spike) to 1.0 (extreme spike ~100% above baseline).
        The spike will appear in the next `get_energy_telemetry` call for this building.
        """
        clamped = max(0.0, min(1.0, severity))
        with _anomaly_lock:
            _injected_anomalies[building_id] = clamped
        return {
            "status": "injected",
            "building_id": building_id,
            "severity": clamped,
            "message": f"Anomaly spike ({clamped:.0%}) queued for building {building_id}.",
        }

"""Tests for the LangGraph agent state machine."""

import pytest

from ecoverify.agents.state import EcoVerifyState
from ecoverify.agents.nodes.vanguard import vanguard_node
from ecoverify.agents.nodes.jurist import jurist_node
from ecoverify.agents.nodes.architect import architect_node
from ecoverify.agents.nodes.finalize import finalize_node
from ecoverify.agents.edges import route_after_vanguard, route_after_jurist

# Inject anomaly before running vanguard tests
from ecoverify.mcp.tools.bms import _injected_anomalies, _anomaly_lock


def _empty_state(**overrides) -> EcoVerifyState:
    """Create a minimal valid state dict."""
    state: EcoVerifyState = {
        "messages": [],
        "telemetry_data": None,
        "anomalies": [],
        "citations": [],
        "decision_traces": [],
        "compliance_report": None,
        "simulation_result": None,
        "jira_tickets": [],
        "governor_approval": None,
        "current_phase": "starting",
        "error_log": [],
        "iteration_count": 0,
        "ui_events": [],
    }
    state.update(overrides)  # type: ignore
    return state


class TestVanguardNode:
    """THE VANGUARD — anomaly detection node."""

    def test_vanguard_returns_required_keys(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ecoverify.config.settings.keys_dir", str(tmp_path))
        state = _empty_state()
        result = vanguard_node(state)

        assert "telemetry_data" in result
        assert "anomalies" in result
        assert "citations" in result
        assert "decision_traces" in result
        assert "ui_events" in result
        assert "messages" in result
        assert len(result["citations"]) == 2  # energy + water
        assert len(result["decision_traces"]) == 1

    def test_vanguard_detects_injected_anomaly(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ecoverify.config.settings.keys_dir", str(tmp_path))
        # Inject a spike
        with _anomaly_lock:
            _injected_anomalies["HQ-01"] = 0.8
        state = _empty_state()
        result = vanguard_node(state)

        assert len(result["anomalies"]) > 0
        assert result["anomalies"][0]["type"] == "energy_spike"

    def test_vanguard_traces_are_signed(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ecoverify.config.settings.keys_dir", str(tmp_path))
        state = _empty_state()
        result = vanguard_node(state)

        trace = result["decision_traces"][0]
        assert trace["agent_id"] == "vanguard"
        assert trace["signature"]
        assert trace["payload_hash"]
        assert len(trace["payload_hash"]) == 64


class TestJuristNode:
    """THE JURIST — compliance evaluation node."""

    def test_citation_failure_triggers_self_correction(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ecoverify.config.settings.keys_dir", str(tmp_path))
        # No citations → should trigger self-correction
        state = _empty_state(citations=[], anomalies=[{"type": "energy_spike"}])
        result = jurist_node(state)

        assert result["current_phase"] == "citation_failure"
        assert len(result["error_log"]) > 0

    def test_compliant_with_valid_citations(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ecoverify.config.settings.keys_dir", str(tmp_path))
        from ecoverify.nhi.middleware import cite_data_source

        citation = cite_data_source("bms:energy:HQ-01", {"readings": [1, 2, 3]})
        anomaly = {
            "type": "energy_spike",
            "building_id": "HQ-01",
            "severity": "high",
            "metric": "+25%",
        }
        state = _empty_state(citations=[citation], anomalies=[anomaly])
        result = jurist_node(state)

        assert result["current_phase"] == "jurist_complete"
        assert result["compliance_report"] is not None
        assert result["compliance_report"]["status"] in ("compliant", "non_compliant")


class TestEdgeRouting:
    """Conditional edge routing functions."""

    def test_route_after_vanguard_with_anomalies(self):
        state = _empty_state(anomalies=[{"type": "energy_spike"}])
        assert route_after_vanguard(state) == "jurist"

    def test_route_after_vanguard_no_anomalies(self):
        state = _empty_state(anomalies=[])
        assert route_after_vanguard(state) == "__end__"

    def test_route_after_jurist_citation_failure(self):
        state = _empty_state(current_phase="citation_failure", iteration_count=1)
        assert route_after_jurist(state) == "vanguard"

    def test_route_after_jurist_max_iterations(self):
        state = _empty_state(current_phase="citation_failure", iteration_count=5)
        assert route_after_jurist(state) == "__end__"

    def test_route_after_jurist_compliant(self):
        state = _empty_state(
            current_phase="jurist_complete",
            compliance_report={"status": "compliant"},
        )
        assert route_after_jurist(state) == "architect"

    def test_route_after_jurist_non_compliant(self):
        state = _empty_state(
            current_phase="jurist_complete",
            compliance_report={"status": "non_compliant"},
        )
        assert route_after_jurist(state) == "governor"


class TestArchitectNode:
    """THE ARCHITECT — ROI simulation node."""

    def test_architect_computes_roi(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ecoverify.config.settings.keys_dir", str(tmp_path))
        anomaly = {
            "type": "energy_spike",
            "building_id": "HQ-01",
            "severity": "high",
            "metric": "+30%",
            "peak_kwh": 200,
            "avg_kwh": 130,
        }
        state = _empty_state(anomalies=[anomaly])
        result = architect_node(state)

        assert result["simulation_result"]["monthly_savings_usd"] > 0
        assert result["simulation_result"]["npv_3yr_usd"] > 0
        assert len(result["jira_tickets"]) == 1
        assert len(result["decision_traces"]) == 1


class TestFinalizeNode:
    """FINALIZE — proof-graph generation and completion."""

    def test_finalize_generates_mermaid(self):
        traces = [
            {"agent_id": "vanguard", "decision": {"action": "scan", "anomalies_found": 1}, "payload_hash": "abc123ef"},
            {"agent_id": "jurist", "decision": {"action": "compliance", "status": "compliant"}, "payload_hash": "def456ab"},
        ]
        state = _empty_state(
            decision_traces=traces,
            anomalies=[{"type": "energy_spike"}],
            simulation_result={"monthly_savings_usd": 14000},
            jira_tickets=[{"ticket_id": "ECO-12345", "status": "Open"}],
            compliance_report={"status": "compliant"},
        )
        result = finalize_node(state)

        assert result["current_phase"] == "complete"
        # Check for proof_graph UI event
        proof_events = [e for e in result["ui_events"] if e["type"] == "proof_graph"]
        assert len(proof_events) == 1
        assert "graph TD" in proof_events[0]["mermaid"]
        assert "VANGUARD" in proof_events[0]["mermaid"]

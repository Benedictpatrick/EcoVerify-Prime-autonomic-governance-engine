"""Tests for MCP tools (BMS, Jira, Regulatory)."""

import pytest

from ecoverify.mcp.tools.bms import register_bms_tools, _injected_anomalies, _anomaly_lock
from ecoverify.mcp.tools.jira_ops import register_jira_tools
from ecoverify.mcp.tools.regulatory import register_regulatory_tools


class _ToolBucket:
    """Collects functions registered via ``@mcp.tool()`` decorator."""
    def __init__(self):
        self._tools: dict = {}
    def tool(self):
        def deco(fn):
            self._tools[fn.__name__] = fn
            return fn
        return deco
    def __getattr__(self, name):
        if name.startswith("_"):
            return super().__getattribute__(name)
        return self._tools[name]


class TestBMSTools:
    """Building Management System telemetry tools."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.bms = _ToolBucket()
        register_bms_tools(self.bms)

    def test_energy_telemetry_schema(self):
        result = self.bms.get_energy_telemetry(building_id="HQ-01", hours=6)
        assert "building_id" in result
        assert result["building_id"] == "HQ-01"
        assert "readings" in result
        assert "summary" in result
        assert len(result["readings"]) == 6
        assert "avg_kwh" in result["summary"]
        assert "peak_kwh" in result["summary"]
        assert "anomaly_count" in result["summary"]

    def test_water_telemetry_schema(self):
        result = self.bms.get_water_telemetry(building_id="HQ-01", hours=4)
        assert result["building_id"] == "HQ-01"
        assert len(result["readings"]) == 4
        assert "avg_gallons" in result["summary"]

    def test_inject_anomaly(self):
        result = self.bms.inject_anomaly(building_id="HQ-02", severity=0.8)
        assert result["status"] == "injected"
        assert result["severity"] == 0.8

        # Verify the anomaly appears in subsequent telemetry
        energy = self.bms.get_energy_telemetry(building_id="HQ-02", hours=6)
        assert energy["summary"]["anomaly_count"] > 0

    def test_severity_clamping(self):
        result = self.bms.inject_anomaly(building_id="HQ-03", severity=5.0)
        assert result["severity"] == 1.0

        result = self.bms.inject_anomaly(building_id="HQ-03", severity=-1.0)
        assert result["severity"] == 0.0


class TestJiraTools:
    """Jira Operations tools."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.jira = _ToolBucket()
        register_jira_tools(self.jira)

    def test_create_ticket(self):
        ticket = self.jira.create_maintenance_ticket(
            title="Test Ticket",
            description="Testing jira tool",
            priority="High",
            building_id="HQ-01",
        )
        assert "ticket_id" in ticket
        assert ticket["ticket_id"].startswith("ECO-")
        assert ticket["status"] == "Open"
        assert ticket["priority"] == "High"
        assert "url" in ticket

    def test_list_open_tickets(self):
        self.jira.create_maintenance_ticket(
            title="Open Ticket",
            description="test",
            building_id="HQ-05",
        )
        tickets = self.jira.list_open_tickets(building_id="HQ-05")
        assert len(tickets) >= 1
        assert all(t["status"] == "Open" for t in tickets)

    def test_update_ticket_status(self):
        ticket = self.jira.create_maintenance_ticket(
            title="Status Test",
            description="test",
        )
        updated = self.jira.update_ticket_status(
            ticket_id=ticket["ticket_id"],
            status="Resolved",
        )
        assert updated["status"] == "Resolved"


class TestRegulatoryTools:
    """EU AI Act compliance tools."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.reg = _ToolBucket()
        register_regulatory_tools(self.reg)

    def test_query_by_keyword(self):
        result = self.reg.query_eu_ai_act(keyword="transparency")
        assert result["result_count"] > 0
        assert len(result["articles"]) > 0

    def test_query_by_section(self):
        result = self.reg.query_eu_ai_act(section="Article 14")
        assert result["result_count"] >= 1
        assert any("14" in a["section"] for a in result["articles"])

    def test_query_all(self):
        result = self.reg.query_eu_ai_act()
        assert result["result_count"] >= 10  # we have 15 articles

    def test_compliance_vector_high_risk(self):
        result = self.reg.check_compliance_vector(
            action_description="Autonomous energy optimization",
            risk_level="high",
        )
        assert result["compliant"] is True
        assert result["requires_human_oversight"] is True
        assert result["risk_classification"] == "high"
        assert "reasoning" in result

    def test_compliance_vector_unacceptable(self):
        result = self.reg.check_compliance_vector(
            action_description="Social scoring system",
            risk_level="unacceptable",
        )
        assert result["compliant"] is False

    def test_compliance_vector_minimal(self):
        result = self.reg.check_compliance_vector(
            action_description="Simple logging",
            risk_level="minimal",
        )
        assert result["compliant"] is True
        assert result["requires_human_oversight"] is False

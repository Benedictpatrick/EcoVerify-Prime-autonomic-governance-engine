"""Jira Operations MCP tools.

Simulates Jira-like ticket management for autonomous maintenance workflows.
In production, these would call the Jira REST API.
"""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone

_ticket_lock = threading.Lock()
_tickets: list[dict] = []


def register_jira_tools(mcp):
    """Register Jira Operations tools on the given FastMCP server instance."""

    @mcp.tool()
    def create_maintenance_ticket(
        title: str,
        description: str,
        priority: str = "Medium",
        assignee: str = "auto",
        building_id: str = "HQ-01",
    ) -> dict:
        """Create a maintenance ticket for a detected anomaly.

        Priority values: Critical, High, Medium, Low.
        Set assignee to 'auto' for intelligent routing.
        """
        ticket_id = f"ECO-{random_ticket_num()}"
        ticket = {
            "ticket_id": ticket_id,
            "title": title,
            "description": description,
            "priority": priority,
            "assignee": assignee if assignee != "auto" else "facilities-team",
            "building_id": building_id,
            "status": "Open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "url": f"https://ecoverify.atlassian.net/browse/{ticket_id}",
        }
        with _ticket_lock:
            _tickets.append(ticket)
        return ticket

    @mcp.tool()
    def list_open_tickets(building_id: str = "HQ-01") -> list[dict]:
        """List all open maintenance tickets for a building."""
        with _ticket_lock:
            return [
                t for t in _tickets
                if t.get("building_id") == building_id and t.get("status") == "Open"
            ]

    @mcp.tool()
    def update_ticket_status(
        ticket_id: str,
        status: str = "In Progress",
    ) -> dict:
        """Update the status of an existing ticket.

        Valid statuses: Open, In Progress, Resolved, Closed.
        """
        with _ticket_lock:
            for t in _tickets:
                if t["ticket_id"] == ticket_id:
                    t["status"] = status
                    t["updated_at"] = datetime.now(timezone.utc).isoformat()
                    return t
        return {"error": f"Ticket {ticket_id} not found."}


def random_ticket_num() -> str:
    return str(uuid.uuid4().int % 90000 + 10000)

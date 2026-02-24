"""FastMCP server — exposes BMS, Jira, and Regulatory tools over streamable HTTP.

Run standalone:
    python -m ecoverify.mcp.server

Or import ``mcp_server`` for in-process testing.
"""

from __future__ import annotations

import logging

from fastmcp import FastMCP

from ecoverify.mcp.tools.bms import register_bms_tools
from ecoverify.mcp.tools.jira_ops import register_jira_tools
from ecoverify.mcp.tools.regulatory import register_regulatory_tools
from ecoverify.mcp.tools.web3_ops import register_web3_tools
from ecoverify.mcp.tools.fintech import register_fintech_tools
from ecoverify.mcp.tools.fhir import register_fhir_tools

logger = logging.getLogger(__name__)

mcp_server = FastMCP(
    "EcoVerify-MCP",
    instructions=(
        "EcoVerify-Prime MCP server.  Provides tools for Building Management System "
        "(BMS) telemetry, Jira Operations (ticket management), EU AI Act "
        "Regulatory Registry queries, Web3/USDC settlement, Fintech risk scoring, "
        "and HL7 FHIR clinical energy auditing."
    ),
)

# Register all tool domains
register_bms_tools(mcp_server)
register_jira_tools(mcp_server)
register_regulatory_tools(mcp_server)
register_web3_tools(mcp_server)
register_fintech_tools(mcp_server)
register_fhir_tools(mcp_server)


def main() -> None:
    """Entry-point for ``python -m ecoverify.mcp.server``."""
    from ecoverify.config import settings

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    logger.info("Starting EcoVerify MCP server on port %d", settings.mcp_server_port)
    mcp_server.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=settings.mcp_server_port,
    )


if __name__ == "__main__":
    main()

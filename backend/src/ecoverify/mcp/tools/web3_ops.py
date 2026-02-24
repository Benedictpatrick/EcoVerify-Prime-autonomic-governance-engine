"""MCP tool registration — Web3 / USDC settlement operations."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def register_web3_tools(server) -> None:
    """Register Web3 settlement tools on *server* (FastMCP or _ToolBucket)."""

    @server.tool()
    def settle_a2a_fee(
        from_agent: str,
        to_agent: str,
        amount_usdc: float,
        memo: str = "",
    ) -> dict:
        """Settle a USDC service fee between two agents on Solana devnet.

        Parameters
        ----------
        from_agent : str
            Payer agent identifier.
        to_agent : str
            Payee agent identifier.
        amount_usdc : float
            Amount in USDC.
        memo : str
            Human-readable memo.
        """
        from ecoverify.web3.models import SettlementRequest
        from ecoverify.web3.settlement import create_settlement

        req = SettlementRequest(
            from_agent=from_agent,
            to_agent=to_agent,
            amount_usdc=amount_usdc,
            memo=memo,
        )
        receipt = create_settlement(req)
        return receipt.model_dump()

    @server.tool()
    def get_settlement_status(tx_signature: str) -> dict:
        """Look up a settlement by transaction signature.

        Parameters
        ----------
        tx_signature : str
            The Solana transaction signature to query.
        """
        from ecoverify.web3.settlement import get_settlement

        receipt = get_settlement(tx_signature)
        if receipt is None:
            return {"status": "not_found", "tx_signature": tx_signature}
        return receipt.model_dump()

    @server.tool()
    def get_agent_balance(agent_id: str) -> dict:
        """Get the USDC balance for an agent wallet.

        Parameters
        ----------
        agent_id : str
            The agent identifier.
        """
        from ecoverify.web3.wallet import get_balance, get_or_create_wallet

        wallet = get_or_create_wallet(agent_id)
        balance = get_balance(agent_id)
        return {
            "agent_id": agent_id,
            "public_key": wallet.public_key,
            "balance_usdc": balance,
            "network": wallet.network,
        }

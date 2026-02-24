"""Solana devnet USDC settlement engine.

Simulates on-chain USDC micro-settlements between agents.  In production
this would use ``solders`` + ``solana-py`` to submit real SPL token
transfer instructions to a Solana RPC endpoint.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone

from ecoverify.config import settings
from ecoverify.web3.models import SettlementReceipt, SettlementRequest
from ecoverify.web3.wallet import credit, debit, get_or_create_wallet

logger = logging.getLogger(__name__)

# ── Settlement ledger (in-memory for devnet simulation) ─────────

_ledger: list[SettlementReceipt] = []


def _mock_tx_signature() -> str:
    """Generate a plausible Solana transaction signature."""
    raw = hashlib.sha256(uuid.uuid4().bytes).hexdigest()
    return raw[:88]


def create_settlement(req: SettlementRequest) -> SettlementReceipt:
    """Execute a USDC settlement between two agents.

    On devnet this is fully simulated with instant confirmation.
    """
    from_wallet = get_or_create_wallet(req.from_agent)
    to_wallet = get_or_create_wallet(req.to_agent)

    # Attempt debit
    if not debit(req.from_agent, req.amount_usdc):
        receipt = SettlementReceipt(
            tx_signature=_mock_tx_signature(),
            from_agent=req.from_agent,
            to_agent=req.to_agent,
            amount_usdc=req.amount_usdc,
            network=settings.solana_network,
            status="failed",
            timestamp=datetime.now(timezone.utc).isoformat(),
            memo=req.memo or "Insufficient USDC balance",
        )
        _ledger.append(receipt)
        logger.warning("Settlement failed: %s → %s ($%.2f USDC) — insufficient balance",
                        req.from_agent, req.to_agent, req.amount_usdc)
        return receipt

    credit(req.to_agent, req.amount_usdc)

    receipt = SettlementReceipt(
        tx_signature=_mock_tx_signature(),
        from_agent=req.from_agent,
        to_agent=req.to_agent,
        amount_usdc=req.amount_usdc,
        network=settings.solana_network,
        status="confirmed",
        timestamp=datetime.now(timezone.utc).isoformat(),
        memo=req.memo or f"A2A service fee: {req.from_agent} → {req.to_agent}",
        block_hash=hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:64],
    )
    _ledger.append(receipt)
    logger.info("Settlement confirmed: %s → %s ($%.4f USDC) tx=%s",
                req.from_agent, req.to_agent, req.amount_usdc, receipt.tx_signature[:16])
    return receipt


def get_settlement(tx_signature: str) -> SettlementReceipt | None:
    """Look up a settlement by transaction signature."""
    for r in _ledger:
        if r.tx_signature == tx_signature:
            return r
    return None


def get_agent_settlements(agent_id: str) -> list[SettlementReceipt]:
    """Return all settlements involving *agent_id*."""
    return [r for r in _ledger if r.from_agent == agent_id or r.to_agent == agent_id]


def get_ledger() -> list[SettlementReceipt]:
    """Return the full settlement ledger."""
    return list(_ledger)

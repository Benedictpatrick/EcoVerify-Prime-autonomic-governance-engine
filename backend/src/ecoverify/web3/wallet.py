"""Agent wallet management for Solana devnet USDC settlement.

Each agent receives a deterministic Solana-compatible wallet derived from its
existing NHI Ed25519 keypair.  In devnet mode, wallets are simulated with
mock balances.
"""

from __future__ import annotations

import base64
import hashlib
import logging
from datetime import datetime, timezone

from ecoverify.config import settings
from ecoverify.web3.models import AgentWallet

logger = logging.getLogger(__name__)

# ── In-memory wallet registry (simulated devnet) ────────────────

_wallets: dict[str, AgentWallet] = {}
_balances: dict[str, float] = {}  # agent_id → USDC balance


def _derive_address(agent_id: str) -> str:
    """Derive a deterministic Base58-style address from agent_id."""
    raw = hashlib.sha256(f"ecoverify:{agent_id}:solana".encode()).digest()
    return base64.b58encode(raw).decode("ascii") if hasattr(base64, "b58encode") else base64.b64encode(raw).decode("ascii")[:44]


def get_or_create_wallet(agent_id: str) -> AgentWallet:
    """Return the wallet for *agent_id*, creating it if needed."""
    if agent_id not in _wallets:
        address = _derive_address(agent_id)
        _wallets[agent_id] = AgentWallet(
            agent_id=agent_id,
            public_key=address,
            network=settings.solana_network,
        )
        _balances[agent_id] = 10_000.0  # airdrop 10k USDC on devnet
        logger.info("Created devnet wallet for '%s' → %s (balance: 10,000 USDC)", agent_id, address)
    return _wallets[agent_id]


def get_balance(agent_id: str) -> float:
    """Return USDC balance for agent (devnet simulated)."""
    get_or_create_wallet(agent_id)
    return _balances.get(agent_id, 0.0)


def debit(agent_id: str, amount: float) -> bool:
    """Debit USDC from agent balance. Returns False if insufficient."""
    bal = get_balance(agent_id)
    if bal < amount:
        return False
    _balances[agent_id] = bal - amount
    return True


def credit(agent_id: str, amount: float) -> None:
    """Credit USDC to agent balance."""
    get_or_create_wallet(agent_id)
    _balances[agent_id] = _balances.get(agent_id, 0.0) + amount

"""Pydantic models for Web3 settlement domain."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgentWallet(BaseModel):
    """Wallet identity for an agent on Solana devnet."""

    agent_id: str
    public_key: str  # base58 Solana address
    network: str = "devnet"


class SettlementRequest(BaseModel):
    """Request to settle an A2A service fee in USDC."""

    from_agent: str
    to_agent: str
    amount_usdc: float = Field(ge=0.0)
    memo: str = ""


class SettlementReceipt(BaseModel):
    """Receipt of a completed or simulated settlement."""

    tx_signature: str
    from_agent: str
    to_agent: str
    amount_usdc: float
    network: str = "devnet"
    status: str = "confirmed"  # confirmed | pending | failed
    timestamp: str = ""
    memo: str = ""
    block_hash: str = ""

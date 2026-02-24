"""Cryptographic Decision Trace — sign and verify agent decisions.

Every autonomous action produces a ``DecisionTrace`` containing:
  • The decision payload (arbitrary JSON-serialisable dict).
  • A SHA-256 hash of the canonical JSON.
  • An Ed25519 signature proving the specific agent produced it.
  • Timestamps and agent identity metadata.

Verification is deterministic — replaying the canonical JSON against the
public key will always yield the same result.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from datetime import datetime, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ── Pydantic models ────────────────────────────────────────────────


class DecisionTrace(BaseModel):
    """Immutable, signed record of an agent decision."""

    agent_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision: dict
    payload_hash: str = ""
    signature: str = ""

    model_config = {"frozen": False}  # we mutate during signing only


class CitationBlock(BaseModel):
    """Proof that a data source was consulted before acting."""

    source_id: str
    data_hash: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    snippet: str = ""  # optional human-readable excerpt


# ── Canonical serialisation ────────────────────────────────────────


def _canonicalise(payload: dict) -> bytes:
    """Deterministic JSON bytes (sorted keys, no whitespace)."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


# ── Signing ────────────────────────────────────────────────────────


def sign_decision_trace(
    agent_id: str,
    decision: dict,
    private_key: Ed25519PrivateKey,
) -> DecisionTrace:
    """Create a cryptographically signed ``DecisionTrace``.

    Parameters
    ----------
    agent_id:
        Identifier of the signing agent (e.g. ``"vanguard"``).
    decision:
        Arbitrary JSON-serialisable dict representing the decision.
    private_key:
        The agent's Ed25519 private key.

    Returns
    -------
    DecisionTrace
        Populated with ``payload_hash`` and ``signature``.
    """
    trace = DecisionTrace(agent_id=agent_id, decision=decision)
    # Canonical payload is everything except signature & hash (they are empty at this point)
    signable = {
        "agent_id": trace.agent_id,
        "timestamp": trace.timestamp,
        "decision": trace.decision,
    }
    canonical = _canonicalise(signable)
    trace.payload_hash = hashlib.sha256(canonical).hexdigest()
    trace.signature = base64.b64encode(private_key.sign(canonical)).decode("ascii")
    logger.debug("Signed decision trace for agent '%s' — hash=%s", agent_id, trace.payload_hash)
    return trace


# ── Verification ───────────────────────────────────────────────────


def verify_decision_trace(trace: DecisionTrace, public_key: Ed25519PublicKey) -> bool:
    """Verify the signature on a ``DecisionTrace``.

    Returns ``True`` if the signature is valid, ``False`` otherwise.
    """
    signable = {
        "agent_id": trace.agent_id,
        "timestamp": trace.timestamp,
        "decision": trace.decision,
    }
    canonical = _canonicalise(signable)

    # Verify hash first (fast check)
    expected_hash = hashlib.sha256(canonical).hexdigest()
    if expected_hash != trace.payload_hash:
        logger.warning("Hash mismatch for trace from '%s'.", trace.agent_id)
        return False

    # Verify Ed25519 signature
    try:
        sig_bytes = base64.b64decode(trace.signature)
        public_key.verify(sig_bytes, canonical)
        return True
    except (InvalidSignature, Exception) as exc:
        logger.warning("Signature verification failed for '%s': %s", trace.agent_id, exc)
        return False

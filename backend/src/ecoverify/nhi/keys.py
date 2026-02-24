"""Ed25519 key generation and management for Non-Human Identity (NHI).

Each agent in the swarm receives a unique Ed25519 keypair.  Private keys are
persisted to disk under ``KEYS_DIR/<agent_id>.pem`` and loaded on demand so
that cryptographic decision traces survive process restarts.
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from ecoverify.config import settings

logger = logging.getLogger(__name__)

# ── Key-pair lifecycle ──────────────────────────────────────────────


def _key_path(agent_id: str) -> Path:
    return settings.keys_path / f"{agent_id}.pem"


def generate_agent_keypair(
    agent_id: str,
    *,
    overwrite: bool = False,
) -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    """Generate and persist an Ed25519 keypair for *agent_id*.

    If the key file already exists and *overwrite* is ``False`` the existing
    key is loaded instead.
    """
    path = _key_path(agent_id)
    if path.exists() and not overwrite:
        logger.info("Key already exists for agent '%s', loading.", agent_id)
        return load_private_key(agent_id), load_public_key(agent_id)

    private_key = Ed25519PrivateKey.generate()
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    path.write_bytes(pem)
    logger.info("Generated new Ed25519 keypair for agent '%s'.", agent_id)
    return private_key, private_key.public_key()


def load_private_key(agent_id: str) -> Ed25519PrivateKey:
    """Load the private key for *agent_id* from disk."""
    path = _key_path(agent_id)
    if not path.exists():
        raise FileNotFoundError(
            f"No private key found for agent '{agent_id}' at {path}. "
            "Call generate_agent_keypair() first."
        )
    pem = path.read_bytes()
    key = serialization.load_pem_private_key(pem, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError(f"Expected Ed25519PrivateKey, got {type(key).__name__}")
    return key


def load_public_key(agent_id: str) -> Ed25519PublicKey:
    """Derive the public key from the stored private key."""
    return load_private_key(agent_id).public_key()


def get_public_key_b64(agent_id: str) -> str:
    """Return the base64-encoded raw public key bytes (32 bytes)."""
    pub = load_public_key(agent_id)
    raw = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(raw).decode("ascii")


def ensure_all_agent_keys() -> None:
    """Generate keypairs for every known agent if they don't already exist."""
    agent_ids = ["vanguard", "jurist", "architect", "governor"]
    for aid in agent_ids:
        generate_agent_keypair(aid)
    logger.info("All agent NHI keys verified/generated.")

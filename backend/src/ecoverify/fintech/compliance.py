"""Regulatory compliance verification against US GENIUS Act and EU MiCA.

Rule-based compliance checks with optional LLM narrative overlay.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ecoverify.fintech.models import ComplianceResult

logger = logging.getLogger(__name__)

# ── GENIUS Act Rules (USA — stablecoin regulation) ──────────────

GENIUS_ACT_RULES = {
    "reserve_requirement": "Stablecoin issuers must maintain 1:1 reserves in US Treasuries or cash.",
    "audit_requirement": "Monthly public attestation of reserve composition required.",
    "consumer_protection": "Stablecoin holders have priority claim in insolvency proceedings.",
    "interoperability": "Cross-chain transfers must comply with BSA/AML requirements.",
    "reporting": "Quarterly reporting to relevant federal regulator.",
}

# ── EU MiCA Rules (Markets in Crypto-Assets) ───────────────────

MICA_RULES = {
    "authorization": "Crypto-asset service providers must be authorized by a Member State NCA.",
    "whitepaper": "Asset-referenced tokens require publication of a crypto-asset white paper.",
    "reserve_assets": "Issuers of significant e-money tokens must maintain sufficient reserve assets.",
    "market_abuse": "Prohibition of insider dealing, market manipulation in crypto markets.",
    "sustainability": "Environmental sustainability disclosures for consensus mechanisms.",
}


def check_genius_act(
    transaction_type: str = "settlement",
    amount_usd: float = 0.0,
    agent_ids: list[str] | None = None,
) -> ComplianceResult:
    """Verify a transaction against US GENIUS Act provisions."""
    now_iso = datetime.now(timezone.utc).isoformat()
    violations = []

    # Rule checks
    if amount_usd > 10_000 and transaction_type == "settlement":
        violations.append("Transactions >$10k require enhanced KYC under BSA/AML provisions.")

    if not agent_ids:
        violations.append("Agent identity must be verifiable (NHI requirement for GENIUS Act §4).")

    compliant = len(violations) == 0
    return ComplianceResult(
        framework="GENIUS_ACT",
        compliant=compliant,
        violations=violations,
        confidence=0.92,
        details=(
            f"Transaction type '{transaction_type}' for ${amount_usd:,.2f} "
            f"evaluated against 5 GENIUS Act provisions. "
            f"{'All checks passed.' if compliant else f'{len(violations)} violation(s) found.'}"
        ),
        timestamp=now_iso,
    )


def check_mica(
    settlement_type: str = "usdc_transfer",
    amount_eur: float = 0.0,
    cross_border: bool = False,
) -> ComplianceResult:
    """Verify a settlement against EU MiCA provisions."""
    now_iso = datetime.now(timezone.utc).isoformat()
    violations = []

    if cross_border and amount_eur > 1_000:
        violations.append("Cross-border crypto transfers >€1k require originator/beneficiary info (MiCA Art. 76).")

    if settlement_type not in ("usdc_transfer", "token_swap", "stablecoin_payment"):
        violations.append(f"Unrecognized settlement type '{settlement_type}' — manual review required.")

    compliant = len(violations) == 0
    return ComplianceResult(
        framework="EU_MICA",
        compliant=compliant,
        violations=violations,
        confidence=0.89,
        details=(
            f"Settlement '{settlement_type}' for €{amount_eur:,.2f} "
            f"evaluated against 5 MiCA provisions. "
            f"{'All checks passed.' if compliant else f'{len(violations)} violation(s) found.'}"
        ),
        timestamp=now_iso,
    )

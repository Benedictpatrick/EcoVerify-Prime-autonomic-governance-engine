"""Cite-Before-Act middleware — agents must cite data sources before proposing actions.

This enforces the security invariant that no agent can propose a state-mutating
action without first proving it consulted a verifiable data source.  Each
citation hashes the source payload so tampering is detectable downstream.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone

from ecoverify.nhi.signing import CitationBlock

logger = logging.getLogger(__name__)


def cite_data_source(
    source_id: str,
    data: dict | list | str,
    *,
    snippet: str = "",
) -> CitationBlock:
    """Hash a data source and return a ``CitationBlock``.

    Parameters
    ----------
    source_id:
        Logical name of the data source (e.g. ``"bms:energy:HQ-01"``).
    data:
        The raw data payload to hash.
    snippet:
        Optional human-readable excerpt for audit display.
    """
    if isinstance(data, (dict, list)):
        raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    else:
        raw = str(data).encode("utf-8")

    data_hash = hashlib.sha256(raw).hexdigest()
    block = CitationBlock(
        source_id=source_id,
        data_hash=data_hash,
        timestamp=datetime.now(timezone.utc).isoformat(),
        snippet=snippet[:200] if snippet else "",
    )
    logger.debug("Cited source '%s' — hash=%s", source_id, data_hash)
    return block


def verify_citations_present(citations: list[CitationBlock]) -> bool:
    """Return ``True`` if at least one valid citation exists."""
    if not citations:
        logger.warning("Cite-Before-Act violation: no citations provided.")
        return False
    for c in citations:
        if not c.data_hash or len(c.data_hash) != 64:
            logger.warning("Invalid citation hash for source '%s'.", c.source_id)
            return False
    return True


def verify_citation_against_data(
    citation: CitationBlock,
    data: dict | list | str,
) -> bool:
    """Re-hash *data* and compare against the stored citation hash."""
    if isinstance(data, (dict, list)):
        raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    else:
        raw = str(data).encode("utf-8")

    computed = hashlib.sha256(raw).hexdigest()
    if computed != citation.data_hash:
        logger.warning(
            "Citation hash mismatch for '%s': expected=%s got=%s",
            citation.source_id,
            citation.data_hash,
            computed,
        )
        return False
    return True

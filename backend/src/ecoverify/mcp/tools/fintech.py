"""MCP tool registration — Fintech risk scoring and compliance."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def register_fintech_tools(server) -> None:
    """Register fintech tools on *server*."""

    @server.tool()
    def assess_financial_risk(
        anomalies_json: str = "[]",
        compliance_status: str = "unknown",
        financial_exposure: float = 0.0,
    ) -> dict:
        """Compute a composite financial risk score.

        Parameters
        ----------
        anomalies_json : str
            JSON array of anomaly dicts.
        compliance_status : str
            Current compliance status (compliant|non_compliant|unknown).
        financial_exposure : float
            Total financial exposure in USD.
        """
        import json
        from ecoverify.fintech.risk_scoring import compute_risk_score

        anomalies = json.loads(anomalies_json) if isinstance(anomalies_json, str) else anomalies_json
        score = compute_risk_score(anomalies, compliance_status, financial_exposure)
        return score.model_dump()

    @server.tool()
    def verify_genius_act_compliance(
        transaction_type: str = "settlement",
        amount_usd: float = 0.0,
    ) -> dict:
        """Verify a transaction against US GENIUS Act.

        Parameters
        ----------
        transaction_type : str
            Type of transaction (settlement, transfer, etc.).
        amount_usd : float
            Transaction amount in USD.
        """
        from ecoverify.fintech.compliance import check_genius_act
        result = check_genius_act(transaction_type, amount_usd)
        return result.model_dump()

    @server.tool()
    def verify_mica_compliance(
        settlement_type: str = "usdc_transfer",
        amount_eur: float = 0.0,
        cross_border: bool = False,
    ) -> dict:
        """Verify a settlement against EU MiCA.

        Parameters
        ----------
        settlement_type : str
            Settlement type.
        amount_eur : float
            Amount in EUR.
        cross_border : bool
            Whether the transfer is cross-border.
        """
        from ecoverify.fintech.compliance import check_mica
        result = check_mica(settlement_type, amount_eur, cross_border)
        return result.model_dump()

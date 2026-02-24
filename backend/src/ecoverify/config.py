"""Centralized configuration via Pydantic Settings (loads from .env)."""

from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings sourced from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── LLM ──────────────────────────────────────────────
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    llm_enabled: bool = True

    # ── Server ───────────────────────────────────────────
    api_port: int = 8000
    mcp_server_port: int = 8001

    # ── Database ─────────────────────────────────────────
    db_path: str = "./ecoverify.db"

    # ── NHI Keys ─────────────────────────────────────────
    keys_dir: str = "./keys"

    # ── OpenTelemetry ────────────────────────────────────
    otel_exporter_otlp_endpoint: str | None = None

    # ── CORS ─────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # ── Web3 / Solana ────────────────────────────────────
    solana_rpc_url: str = "https://api.devnet.solana.com"
    solana_network: str = "devnet"

    # ── FHIR ─────────────────────────────────────────────
    fhir_base_url: str = "http://hapi.fhir.org/baseR4"

    # ── Derived ──────────────────────────────────────────
    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def keys_path(self) -> Path:
        p = Path(self.keys_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def database_path(self) -> Path:
        return Path(self.db_path)


settings = Settings()

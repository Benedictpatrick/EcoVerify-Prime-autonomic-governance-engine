"""FastAPI application entry point for EcoVerify-Prime.

Run with:
    uvicorn ecoverify.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ecoverify.api.routes import router
from ecoverify.api.demo import router as demo_router
from ecoverify.config import settings
from ecoverify.nhi.keys import ensure_all_agent_keys
from ecoverify.telemetry.tracing import init_telemetry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # ── Startup ─────────────────────────────────────────
    logger.info("EcoVerify-Prime starting up…")
    init_telemetry()
    ensure_all_agent_keys()
    logger.info("Ready — API on port %d", settings.api_port)
    yield
    # ── Shutdown ────────────────────────────────────────
    logger.info("EcoVerify-Prime shutting down.")


app = FastAPI(
    title="EcoVerify-Prime",
    description="Autonomic Sustainability Governance Ecosystem",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──────────────────────────────────────────────────────────

app.include_router(router)
app.include_router(demo_router)


# ── Health check ────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ecoverify-prime"}

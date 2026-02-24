# EcoVerify-Prime

**Autonomic Sustainability Governance Ecosystem**

A production-ready, autonomous multi-agent system that monitors enterprise energy/water data via the Model Context Protocol (MCP), audits findings against the EU AI Act (2026 v2), and proposes optimizations with 3D ROI simulations.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  React 19 Dashboard (Tailwind 4 + Three.js + Framer Motion) │
│  ┌──────────┐ ┌──────────────┐ ┌────────────────────────┐  │
│  │ 3D Twin  │ │ Neural Feed  │ │ Governor HITL Panel    │  │
│  └──────────┘ └──────────────┘ └────────────────────────┘  │
│  └─────────── Proof-Graph (Mermaid.js) ──────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │ SSE (Server-Sent Events)
┌──────────────────────────▼──────────────────────────────────┐
│  FastAPI Gateway (SSE Streaming + REST)                      │
├──────────────────────────────────────────────────────────────┤
│  LangGraph Cyclic State Machine                              │
│  ┌──────────┐   ┌─────────┐   ┌───────────┐   ┌──────────┐│
│  │ VANGUARD │──▶│ JURIST  │──▶│ ARCHITECT │──▶│ GOVERNOR ││
│  │ (Monitor)│◀──│(Comply) │   │(Simulate) │◀──│  (HITL)  ││
│  └──────────┘   └─────────┘   └───────────┘   └──────────┘│
│       │              │              │               │       │
│       └──────────────┴──────────────┴───────────────┘       │
│                    NHI Signing (Ed25519)                      │
├──────────────────────────────────────────────────────────────┤
│  FastMCP 3.x Tool Server                                     │
│  ┌─────┐  ┌──────────┐  ┌────────────────────┐             │
│  │ BMS │  │ Jira Ops │  │ Regulatory Registry│             │
│  └─────┘  └──────────┘  └────────────────────┘             │
└──────────────────────────────────────────────────────────────┘
```

## Agent Swarm

| Agent | Role | Node |
|-------|------|------|
| **VANGUARD** | Autonomous anomaly detection in BMS telemetry | `monitor_node` |
| **JURIST** | EU AI Act v2 compliance evaluation (System 2 reasoning) | `compliance_node` |
| **ARCHITECT** | What-If ROI analysis + 3D visualization data | `simulation_node` |
| **GOVERNOR** | Mandatory HITL breakpoint for state-mutating actions | `hitl_node` |

## Quick Start

```bash
# 1. Clone & configure
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# 2. Backend
cd backend
uv sync
uv run uvicorn ecoverify.main:app --reload --port 8000

# 3. MCP Server (separate terminal)
cd backend
uv run python -m ecoverify.mcp.server

# 4. Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` — click **Trigger Anomaly** to start the demo flow.

## Key Features

- **Durable Orchestration**: LangGraph with SQLite checkpointing (Temporal-style persistence)
- **Model Context Protocol**: FastMCP 3.x server exposing BMS, Jira, and Regulatory tools
- **Zero-Trust NHI**: Ed25519 cryptographic decision traces on every agent action
- **Cite-Before-Act**: Agents cannot propose actions without verified data hashes
- **Generative UI**: Structured JSON events streamed via SSE → React spawns components
- **3D Digital Twin**: Three.js facility visualization with real-time energy node updates
- **Proof-Graph**: Mermaid.js rendering of the agent reasoning chain
- **OpenTelemetry**: Full distributed tracing of agent interactions

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Orchestration | LangGraph 1.x (cyclic state machine) |
| LLM | OpenAI GPT-4o via langchain-openai |
| Tool Protocol | FastMCP 3.x (streamable HTTP) |
| Signing | Ed25519 (cryptography lib) |
| API | FastAPI + sse-starlette |
| Frontend | React 19 + Tailwind CSS 4 + Vite 6 |
| 3D | Three.js / React Three Fiber |
| Animations | Framer Motion 11 |
| Graphs | Mermaid.js |
| State | Zustand |
| Tracing | OpenTelemetry SDK |

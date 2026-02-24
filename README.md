EcoVerify-Prime
Autonomic Sustainability Governance Ecosystem

EcoVerify-Prime is a production-grade autonomous multi-agent platform for enterprise sustainability governance. The system continuously monitors energy and water telemetry, evaluates regulatory compliance against the EU AI Act (2026 v2), and proposes optimization strategies supported by interactive 3D ROI simulations.

The platform combines deterministic agent orchestration, cryptographically verifiable decision traces, and generative user interfaces to deliver auditable, explainable, and actionable sustainability intelligence.

+-----------------------------------------------------------+
| React Dashboard (Tailwind + Three.js + Framer Motion)     |
|                                                           |
|  +--------+   +------------+   +----------------------+   |
|  | 3D Twin|   | NeuralFeed |   | Governor HITL Panel  |   |
|  +--------+   +------------+   +----------------------+   |
|                                                           |
|        Proof Graph (Mermaid)                              |
+--------------------------+--------------------------------+
                           |
                           |  SSE
                           v
+-----------------------------------------------------------+
| FastAPI Gateway (REST + Streaming)                        |
+-----------------------------------------------------------+
| LangGraph Cyclic State Machine                            |
|                                                           |
|  VANGUARD --> JURIST --> ARCHITECT --> GOVERNOR           |
|     ^                                  |                  |
|     +----------------------------------+                  |
|                                                           |
|            Ed25519 Decision Signing                       |
+-----------------------------------------------------------+
| MCP Tool Server                                           |
|   BMS     |    Jira Ops    |    Regulatory Registry       |
+-----------------------------------------------------------+





| Agent         | Responsibility                                                        | Execution Node    |
| ------------- | --------------------------------------------------------------------- | ----------------- |
| **VANGUARD**  | Autonomous anomaly detection across BMS telemetry streams             | `monitor_node`    |
| **JURIST**    | EU AI Act v2 compliance reasoning and regulatory validation           | `compliance_node` |
| **ARCHITECT** | Scenario simulation, ROI estimation, and visualization data synthesis | `simulation_node` |
| **GOVERNOR**  | Human-in-the-loop control point for state-mutating actions            | `hitl_node`       |




Quick Start
1. Environment Setup
cp .env.example .env
# Configure OPENAI_API_KEY and other environment variables
2. Backend
cd backend
uv sync
uv run uvicorn ecoverify.main:app --reload --port 8000
3. MCP Server
cd backend
uv run python -m ecoverify.mcp.server
4. Frontend
cd frontend
npm install
npm run dev

Access the application at:

http://localhost:5173

Trigger the demonstration flow by selecting Trigger Anomaly within the dashboard.


Core Capabilities

Durable multi-agent orchestration via LangGraph cyclic state machines

Model Context Protocol integration through FastMCP tool servers

Ed25519 cryptographic signing of agent reasoning and actions

Cite-before-act enforcement ensuring evidence-backed decisions

Generative UI rendering from structured SSE event streams

Real-time 3D Digital Twin facility visualization

Mermaid Proof-Graph of reasoning lineage

Full distributed tracing using OpenTelemetry

Technology Stack
| Layer               | Technology                       |
| ------------------- | -------------------------------- |
| Agent Orchestration | LangGraph 1.x                    |
| LLM Integration     | OpenAI GPT-4o via LangChain      |
| Tool Protocol       | FastMCP 3.x                      |
| API Gateway         | FastAPI + sse-starlette          |
| Signing             | Ed25519 (cryptography)           |
| Frontend            | React 19, Tailwind CSS 4, Vite 6 |
| Visualization       | Three.js / React Three Fiber     |
| Animations          | Framer Motion 11                 |
| State Management    | Zustand                          |
| Graph Rendering     | Mermaid.js                       |
| Observability       | OpenTelemetry SDK                |

Design Principles

Deterministic autonomy with explicit governance boundaries

Cryptographic auditability of all agent decisions

Human-centered oversight through HITL breakpoints

Evidence-linked reasoning chains

Streaming-first generative interface architecture

Interoperable enterprise tool integration via MCP


License


License

Breakform




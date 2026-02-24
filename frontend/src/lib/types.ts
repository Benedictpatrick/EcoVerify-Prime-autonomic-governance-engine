/**
 * Shared TypeScript interfaces for EcoVerify-Prime.
 *
 * Mirror of backend Pydantic models + frontend-specific types.
 */

// ── SSE Events ────────────────────────────────────────────────────

export interface SSEEvent {
  type: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

// ── Neural Feed ───────────────────────────────────────────────────

export type AgentName = "VANGUARD" | "JURIST" | "ARCHITECT" | "GOVERNOR" | "SYSTEM" | "FHIR" | "FINTECH" | "EDUTECH";
export type Severity = "low" | "medium" | "high" | "critical";

export interface NeuralFeedEntry {
  id: string;
  agent: AgentName;
  message: string;
  severity: Severity;
  timestamp: string;
  feedType?: string; // neural_feed | edutech_hint | settlement_update | risk_alert | fhir_audit
}

// ── Decision Trace (NHI) ──────────────────────────────────────────

export interface DecisionTrace {
  agent_id: string;
  timestamp: string;
  decision: Record<string, unknown>;
  payload_hash: string;
  signature: string;
  verified?: boolean;
}

// ── Governor Panel ────────────────────────────────────────────────

export interface GovernorAction {
  action_summary: string;
  estimated_roi: number;
  npv_3yr: number;
  payback_months: number;
  requires_approval: boolean;
  co2_tons_saved_annual?: number;
  env_reduction_pct?: number;
  campus_buildings?: number;
}

// ── 3D Scene ──────────────────────────────────────────────────────

export interface SceneNode {
  id: string;
  position: { x: number; y: number; z: number };
  energy_level: number;
  status: "normal" | "anomaly";
  color: string;
}

export interface SceneConnection {
  from: string;
  to: string;
}

export interface SceneData {
  nodes: SceneNode[];
  connections: SceneConnection[];
}

// ── Web3 / Settlements ────────────────────────────────────────────

export interface Settlement {
  tx_signature: string;
  from_agent: string;
  to_agent: string;
  amount_usdc: number;
  network: string;
  status: string;
  timestamp: string;
  memo: string;
  block_hash: string;
}

// ── Fintech / Risk ────────────────────────────────────────────────

export interface RiskAlert {
  score: number;
  category: string;
  severity: "critical" | "high" | "medium" | "low";
  source: string;
  factors: Array<{ name: string; score: number; weight: number }>;
  recommendation: string;
  timestamp: string;
}

// ── Health / FHIR ─────────────────────────────────────────────────

export interface FHIRAudit {
  facility_id: string;
  facility_type: string;
  energy_efficiency_score: number;
  benchmark_percentile: number;
  recommendations: string[];
  compliance_status: string;
  timestamp: string;
}

// ── Edutech ───────────────────────────────────────────────────────

export interface EdutechHint {
  topic: string;
  urgency: string;
  content: string;
  related_articles: string[];
  estimated_minutes: number;
  timestamp: string;
}

// ── Media Intelligence / Dashboard Config ─────────────────────────

export interface DashboardConfig {
  panel_order: string[];
  emphasis: string;
  detail_level: string;
  auto_expand_proof_graph: boolean;
  highlight_anomalies: boolean;
  show_settlements: boolean;
  theme_accent: string;
}

// ── Transactions Table ────────────────────────────────────────────

export interface TransactionRow {
  id: string;
  description: string;
  time: string;
  currency: string;
  status: "Successful" | "Pending" | "Cancelled";
  cashback: string;
  amount: string;
  source: "settlement" | "jira" | "agent";
}

// ── API Responses ─────────────────────────────────────────────────

export interface RunResponse {
  thread_id: string;
  status: string;
}

export interface GraphStatus {
  thread_id: string;
  phase: string;
  is_running: boolean;
  is_interrupted: boolean;
  anomaly_count: number;
  compliance_status: string;
  monthly_savings: number;
  risk_score: number;
  settlement_count: number;
  fhir_audit_status: string;
}

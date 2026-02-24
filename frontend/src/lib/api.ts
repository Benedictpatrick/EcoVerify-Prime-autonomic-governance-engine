/**
 * API client functions for EcoVerify-Prime backend.
 */

import type { GraphStatus, RunResponse, Settlement, DashboardConfig } from "./types";

const BASE = "/api";

interface AgentCard {
  name: string;
  description: string;
  capabilities: string[];
  url: string;
}

export async function startRun(buildingId = "HQ-01"): Promise<RunResponse> {
  const res = await fetch(`${BASE}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ building_id: buildingId }),
  });
  if (!res.ok) throw new Error(`startRun failed: ${res.status}`);
  return res.json();
}

export async function resumeRun(
  threadId: string,
  approved: boolean,
  roiAdjustment = 1.0
): Promise<{ thread_id: string; status: string }> {
  // Demo mode uses its own resume endpoint (no-op, auto-approves)
  const url =
    threadId === "demo"
      ? `${BASE}/demo/resume`
      : `${BASE}/resume/${threadId}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      thread_id: threadId,
      approved,
      roi_adjustment: roiAdjustment,
    }),
  });
  if (!res.ok) throw new Error(`resumeRun failed: ${res.status}`);
  return res.json();
}

export async function getStatus(threadId: string): Promise<GraphStatus> {
  const res = await fetch(`${BASE}/status/${threadId}`);
  if (!res.ok) throw new Error(`getStatus failed: ${res.status}`);
  return res.json();
}

export async function injectAnomaly(
  buildingId = "HQ-01",
  severity = 0.6
): Promise<{ status: string }> {
  const res = await fetch(`${BASE}/inject-anomaly`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ building_id: buildingId, severity }),
  });
  if (!res.ok) throw new Error(`injectAnomaly failed: ${res.status}`);
  return res.json();
}

export async function getTraces(
  threadId: string
): Promise<{ traces: Array<Record<string, unknown>>; count: number }> {
  const res = await fetch(`${BASE}/traces/${threadId}`);
  if (!res.ok) throw new Error(`getTraces failed: ${res.status}`);
  return res.json();
}

/* ─── New domain endpoints ─── */

export async function getSettlements(
  threadId: string
): Promise<{ settlements: Settlement[] }> {
  const res = await fetch(`${BASE}/settlements/${threadId}`);
  if (!res.ok) throw new Error(`getSettlements failed: ${res.status}`);
  return res.json();
}

export async function personalizeLayout(
  telemetry: Record<string, unknown>
): Promise<{ config: DashboardConfig }> {
  const res = await fetch(`${BASE}/personalize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(telemetry),
  });
  if (!res.ok) throw new Error(`personalizeLayout failed: ${res.status}`);
  return res.json();
}

export async function getAgentCards(): Promise<{ agents: AgentCard[] }> {
  const res = await fetch(`${BASE}/a2a/agents`);
  if (!res.ok) throw new Error(`getAgentCards failed: ${res.status}`);
  return res.json();
}

export async function startDemo(): Promise<RunResponse> {
  const res = await fetch(`${BASE}/demo/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  if (!res.ok) throw new Error(`startDemo failed: ${res.status}`);
  return res.json();
}

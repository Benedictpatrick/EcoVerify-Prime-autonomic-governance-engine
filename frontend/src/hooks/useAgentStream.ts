/**
 * useAgentStream — SSE hook that connects to the backend and dispatches
 * events to the Zustand store.
 *
 * Uses @microsoft/fetch-event-source for robust SSE with POST support
 * and auto-reconnection.
 */

import { useCallback, useRef } from "react";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import { useAgentStore } from "../stores/agentStore";
import type { GovernorAction, NeuralFeedEntry, SceneData, Settlement, RiskAlert, EdutechHint } from "../lib/types";

let idCounter = 0;

export function useAgentStream() {
  const abortRef = useRef<AbortController | null>(null);
  const store = useAgentStore();

  /** Internal helper — opens SSE on the given URL */
  const _open = useCallback(
    (url: string, threadId: string) => {
      abortRef.current?.abort();
      const ctrl = new AbortController();
      abortRef.current = ctrl;

      store.setThreadId(threadId);
      store.setIsRunning(true);

      fetchEventSource(url, {
        signal: ctrl.signal,

        onmessage(ev) {
          if (!ev.data) return;

          try {
            const data = JSON.parse(ev.data);
            const eventType = ev.event || data.type;

            switch (eventType) {
              case "neural_feed": {
                const entry: NeuralFeedEntry = {
                  id: `nf-${++idCounter}`,
                  agent: data.agent ?? "SYSTEM",
                  message: data.message ?? "",
                  severity: data.severity ?? "low",
                  timestamp: data.timestamp ?? new Date().toISOString(),
                  feedType: "neural_feed",
                };
                store.addFeedEntry(entry);
                break;
              }

              case "3d_update": {
                const scene: SceneData = data.payload ?? data;
                store.updateScene(scene);
                break;
              }

              case "proof_graph": {
                store.setProofGraph(data.mermaid ?? "");
                break;
              }

              case "governor_panel": {
                const action: GovernorAction = {
                  action_summary: data.action_summary ?? "",
                  estimated_roi: data.estimated_roi ?? 0,
                  npv_3yr: data.npv_3yr ?? 0,
                  payback_months: data.payback_months ?? 0,
                  requires_approval: data.requires_approval ?? true,
                  co2_tons_saved_annual: data.co2_tons_saved_annual ?? 0,
                  env_reduction_pct: data.env_reduction_pct ?? 0,
                  campus_buildings: data.campus_buildings ?? 1,
                };
                store.setGovernorAction(action);
                break;
              }

              case "interrupt": {
                store.setCurrentPhase("interrupted");
                break;
              }

              case "phase_change": {
                if (data.phase) {
                  store.setCurrentPhase(data.phase);
                  // Auto-clear governor card when auto-approved (demo mode)
                  if (data.phase === "governor_approved") {
                    store.setGovernorAction(null);
                  }
                }
                break;
              }

              case "settlement_update": {
                if (data.settlement) {
                  const settlement: Settlement = data.settlement;
                  store.addSettlement(settlement);
                }
                // Also add to neural feed
                store.addFeedEntry({
                  id: `nf-${++idCounter}`,
                  agent: "SYSTEM",
                  message: data.message ?? "Settlement processed",
                  severity: data.severity ?? "low",
                  timestamp: data.timestamp ?? new Date().toISOString(),
                  feedType: "settlement_update",
                });
                break;
              }

              case "risk_alert": {
                if (data.risk_score) {
                  const risk: RiskAlert = data.risk_score;
                  store.addRiskAlert(risk);
                }
                store.addFeedEntry({
                  id: `nf-${++idCounter}`,
                  agent: "SYSTEM",
                  message: data.message ?? "Risk alert",
                  severity: data.severity ?? "medium",
                  timestamp: data.timestamp ?? new Date().toISOString(),
                  feedType: "risk_alert",
                });
                break;
              }

              case "edutech_hint": {
                if (data.hint) {
                  const hint: EdutechHint = data.hint;
                  store.addEdutechHint(hint);
                }
                store.addFeedEntry({
                  id: `nf-${++idCounter}`,
                  agent: "SYSTEM",
                  message: data.message ?? "Learning recommendation",
                  severity: "low",
                  timestamp: data.timestamp ?? new Date().toISOString(),
                  feedType: "edutech_hint",
                });
                break;
              }

              case "fhir_audit": {
                store.addFeedEntry({
                  id: `nf-${++idCounter}`,
                  agent: "SYSTEM",
                  message: data.message ?? "FHIR audit update",
                  severity: data.severity ?? "low",
                  timestamp: data.timestamp ?? new Date().toISOString(),
                  feedType: "fhir_audit",
                });
                break;
              }

              case "layout_hint": {
                if (data.config) {
                  store.setDashboardConfig(data.config);
                }
                break;
              }

              case "execution_complete":
              case "complete": {
                store.setIsRunning(false);
                store.setCurrentPhase("complete");
                break;
              }

              default:
                if (data.phase) {
                  store.setCurrentPhase(data.phase);
                }
            }
          } catch {
            // Ignore parse errors
          }
        },

        onerror(err) {
          console.warn("[SSE] error:", err);
        },

        onclose() {
          store.setIsRunning(false);
        },
      });
    },
    [store]
  );

  /** Connect to the real pipeline SSE stream */
  const connect = useCallback(
    (threadId: string) => _open(`/api/stream/${threadId}`, threadId),
    [_open]
  );

  /** Connect to the pre-scripted demo SSE stream */
  const connectDemo = useCallback(
    () => _open("/api/demo/stream", "demo"),
    [_open]
  );

  const disconnect = useCallback(() => {
    abortRef.current?.abort();
    store.setIsRunning(false);
  }, [store]);

  return { connect, connectDemo, disconnect };
}

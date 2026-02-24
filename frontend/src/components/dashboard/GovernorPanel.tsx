/**
 * GovernorPanel — right sidebar HITL approval panel.
 *
 * Renders inside the dashboard-side grid area. Shows idle summary when
 * no approval is needed; shows action card with ROI slider when interrupted.
 */

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAgentStore } from "../../stores/agentStore";
import { resumeRun } from "../../lib/api";

export default function GovernorPanel() {
  const governorAction = useAgentStore((s) => s.governorAction);
  const threadId = useAgentStore((s) => s.threadId);
  const currentPhase = useAgentStore((s) => s.currentPhase);
  const riskAlerts = useAgentStore((s) => s.riskAlerts);
  const settlements = useAgentStore((s) => s.settlements);
  const setGovernorAction = useAgentStore((s) => s.setGovernorAction);
  const [roiAdjustment, setRoiAdjustment] = useState(1.0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleDecision = useCallback(
    async (approved: boolean) => {
      if (!threadId || isSubmitting) return;
      setIsSubmitting(true);
      try {
        await resumeRun(threadId, approved, roiAdjustment);
        setGovernorAction(null);
      } catch (e) {
        console.error("[Governor] Resume failed:", e);
      } finally {
        setIsSubmitting(false);
      }
    },
    [threadId, roiAdjustment, isSubmitting, setGovernorAction]
  );

  const latestRisk = riskAlerts.length > 0 ? riskAlerts[riskAlerts.length - 1] : null;

  return (
    <div className="panel-right dashboard-side flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center gap-2 pb-3 border-b border-zinc-800/50">
        <span className="text-xs font-semibold text-zinc-300">Governor</span>
        <span className="text-[9px] font-mono text-zinc-600 uppercase">
          {currentPhase === "interrupted" ? "Action Required" : "Monitoring"}
        </span>
        <div
          className={`ml-auto status-dot ${
            currentPhase === "interrupted" ? "status-dot-warn" : "status-dot-idle"
          }`}
        />
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="card-sm text-center">
          <div className="text-lg font-bold text-zinc-200">
            {settlements.length}
          </div>
          <div className="metric-label">Settlements</div>
        </div>
        <div className="card-sm text-center">
          <div className={`text-lg font-bold ${latestRisk && latestRisk.score > 0.7 ? "text-red-400" : "text-zinc-200"}`}>
            {latestRisk ? latestRisk.score.toFixed(1) : "—"}
          </div>
          <div className="metric-label">Risk Score</div>
        </div>
      </div>

      {/* Approval card */}
      <AnimatePresence>
        {governorAction && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="card-sm border border-amber-500/20"
          >
            {/* Action header */}
            <div className="flex items-center gap-2 mb-3">
              <div className="w-7 h-7 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
                <span className="text-sm">🛡</span>
              </div>
              <div>
                <h4 className="text-xs font-semibold text-amber-400">
                  Approval Required
                </h4>
                <p className="text-[9px] text-zinc-600">HITL checkpoint</p>
              </div>
              <div className="ml-auto w-2 h-2 rounded-full bg-amber-400 animate-pulse-glow" />
            </div>

            {/* Summary */}
            <p className="text-[11px] text-zinc-400 leading-relaxed mb-3">
              {governorAction.action_summary}
            </p>

            {/* Metrics */}
            <div className="grid grid-cols-2 gap-2 mb-3">
              <div className="text-center p-2 rounded-lg bg-zinc-900/60">
                <div className="text-sm font-bold text-green-400">
                  ${governorAction.estimated_roi.toLocaleString()}
                </div>
                <div className="text-[8px] text-zinc-600 mt-0.5">Monthly</div>
              </div>
              <div className="text-center p-2 rounded-lg bg-zinc-900/60">
                <div className="text-sm font-bold text-blue-400">
                  ${governorAction.npv_3yr.toLocaleString()}
                </div>
                <div className="text-[8px] text-zinc-600 mt-0.5">3Y NPV</div>
              </div>
              <div className="text-center p-2 rounded-lg bg-zinc-900/60">
                <div className="text-sm font-bold text-purple-400">
                  {governorAction.payback_months}mo
                </div>
                <div className="text-[8px] text-zinc-600 mt-0.5">Payback</div>
              </div>
              <div className="text-center p-2 rounded-lg bg-zinc-900/60">
                <div className="text-sm font-bold text-teal-400">
                  {governorAction.co2_tons_saved_annual
                    ? `${governorAction.co2_tons_saved_annual.toFixed(1)}t`
                    : "—"}
                </div>
                <div className="text-[8px] text-zinc-600 mt-0.5">CO₂/yr</div>
              </div>
            </div>

            {/* ROI Slider */}
            <div className="mb-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[9px] text-zinc-500 uppercase tracking-wider">
                  ROI Adjustment
                </span>
                <span className="text-xs font-mono text-amber-400">
                  ×{roiAdjustment.toFixed(2)}
                </span>
              </div>
              <input
                type="range"
                title="ROI Adjustment Factor"
                min="0.5"
                max="1.5"
                step="0.05"
                value={roiAdjustment}
                onChange={(e) => setRoiAdjustment(parseFloat(e.target.value))}
                className="w-full h-1 rounded-full appearance-none bg-zinc-800 outline-none
                  [&::-webkit-slider-thumb]:appearance-none
                  [&::-webkit-slider-thumb]:w-3.5
                  [&::-webkit-slider-thumb]:h-3.5
                  [&::-webkit-slider-thumb]:rounded-full
                  [&::-webkit-slider-thumb]:bg-amber-400
                  [&::-webkit-slider-thumb]:cursor-pointer"
              />
            </div>

            {/* Buttons */}
            <div className="flex gap-2">
              <button
                onClick={() => handleDecision(true)}
                disabled={isSubmitting}
                className="flex-1 py-2 rounded-lg bg-green-500/15 text-green-400
                  hover:bg-green-500/25 text-[10px] font-semibold uppercase tracking-wider
                  border border-green-500/20 transition-all disabled:opacity-50"
              >
                {isSubmitting ? "…" : "✓ Execute"}
              </button>
              <button
                onClick={() => handleDecision(false)}
                disabled={isSubmitting}
                className="px-4 py-2 rounded-lg border border-red-500/20 text-red-400
                  hover:bg-red-500/10 text-[10px] font-semibold uppercase tracking-wider
                  transition-all disabled:opacity-50"
              >
                ✕
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* No-approval idle view */}
      {!governorAction && (
        <div className="card-sm text-center">
          <p className="text-[10px] text-zinc-600 italic">
            No actions pending
          </p>
        </div>
      )}

      {/* Risk alerts feed */}
      {riskAlerts.length > 0 && (
        <div>
          <h4 className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mb-2">
            Risk Alerts
          </h4>
          <div className="flex flex-col gap-1.5 max-h-48 overflow-y-auto">
            {riskAlerts
              .slice(-5)
              .reverse()
              .map((r, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-zinc-900/40"
                >
                  <div
                    className={`w-1.5 h-1.5 rounded-full ${
                      r.severity === "critical"
                        ? "bg-red-500"
                        : r.severity === "high"
                        ? "bg-orange-500"
                        : "bg-amber-500"
                    }`}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-[10px] text-zinc-400 truncate">
                      {r.source}
                    </p>
                    <span className="text-[9px] text-zinc-600">
                      Score: {r.score.toFixed(2)}
                    </span>
                  </div>
                  <span
                    className={`text-[8px] font-mono ${
                      r.severity === "critical" ? "text-red-400" : "text-zinc-500"
                    }`}
                  >
                    {r.severity}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

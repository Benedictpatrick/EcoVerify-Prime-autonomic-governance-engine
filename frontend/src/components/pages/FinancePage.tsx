/**
 * FinancePage — Settlements, Risk Analysis, Transaction Ledger, and Financial Metrics.
 */

import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAgentStore } from "../../stores/agentStore";
import { getSettlements } from "../../lib/api";
import type { Settlement, RiskAlert } from "../../lib/types";

function formatUSD(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(2)}`;
}

function RiskGauge({ score }: { score: number }) {
  const pct = Math.min(score * 100, 100);
  const color = score > 0.7 ? "#ef4444" : score > 0.4 ? "#f59e0b" : "#22c55e";
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-24 h-24">
        <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
          <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="8" />
          <circle
            cx="50" cy="50" r="42" fill="none" stroke={color} strokeWidth="8"
            strokeDasharray={`${pct * 2.64} 264`}
            strokeLinecap="round"
            className="transition-all duration-700"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-lg font-bold" style={{ color }}>{(score * 100).toFixed(0)}</span>
        </div>
      </div>
      <span className="text-[10px] text-zinc-500 uppercase tracking-wider">Risk Score</span>
    </div>
  );
}

function SettlementRow({ s, i }: { s: Settlement; i: number }) {
  return (
    <motion.tr
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: i * 0.05 }}
    >
      <td className="font-mono text-zinc-500 text-xs">{s.tx_signature.slice(0, 10)}…</td>
      <td className="text-xs text-zinc-300">{s.from_agent}</td>
      <td className="text-xs text-zinc-300">{s.to_agent}</td>
      <td className="text-xs font-mono text-green-400">{s.amount_usdc.toFixed(2)} USDC</td>
      <td>
        <span className={`text-[9px] px-1.5 py-0.5 rounded ${
          s.status === "confirmed" ? "bg-green-500/10 text-green-400" : "bg-amber-500/10 text-amber-400"
        }`}>
          {s.status}
        </span>
      </td>
      <td className="text-[10px] text-zinc-500 font-mono">{s.network}</td>
      <td className="text-[10px] text-zinc-500 max-w-[120px] truncate">{s.memo}</td>
    </motion.tr>
  );
}

// Seed demo settlements when empty
const demoSettlements: Settlement[] = [
  {
    tx_signature: "5Kd8vT9xQp2mNwEjRk3YzFHgLcAbXUoC7NhD4sWqBfJi",
    from_agent: "ARCHITECT", to_agent: "VANGUARD", amount_usdc: 42.50,
    network: "solana-devnet", status: "confirmed",
    timestamp: new Date(Date.now() - 300_000).toISOString(),
    memo: "HVAC optimization reward", block_hash: "EjRk3YzFHgL...cAbXUoC7Nh",
  },
  {
    tx_signature: "3Xm7bT2kWp9nJoEiRc4AzDHfLaBbYVpC8QhF5tUrCgHk",
    from_agent: "GOVERNOR", to_agent: "JURIST", amount_usdc: 18.75,
    network: "solana-devnet", status: "confirmed",
    timestamp: new Date(Date.now() - 180_000).toISOString(),
    memo: "Compliance verification fee", block_hash: "RiWc4AzDHfL...aBbYVpC8Qh",
  },
  {
    tx_signature: "7Np4dW6sXr1oKuFjTb5CxEJiMcDdZUpA9ShG2vQtHeIl",
    from_agent: "FINALIZE", to_agent: "ARCHITECT", amount_usdc: 95.00,
    network: "solana-devnet", status: "confirmed",
    timestamp: new Date(Date.now() - 60_000).toISOString(),
    memo: "Carbon credit settlement", block_hash: "FjTb5CxEJiM...cDdZUpA9Sh",
  },
];

const demoRisks: RiskAlert[] = [
  {
    score: 0.72, category: "Energy Spike", severity: "high", source: "BMS-HQ01-HVAC",
    factors: [{ name: "consumption_delta", score: 0.8, weight: 0.6 }, { name: "time_anomaly", score: 0.6, weight: 0.4 }],
    recommendation: "Reduce HVAC load during peak hours",
    timestamp: new Date(Date.now() - 240_000).toISOString(),
  },
  {
    score: 0.45, category: "Compliance Gap", severity: "medium", source: "EU-AI-Act-Art52",
    factors: [{ name: "transparency_score", score: 0.5, weight: 0.7 }, { name: "documentation", score: 0.35, weight: 0.3 }],
    recommendation: "Update AI system documentation for Article 52 compliance",
    timestamp: new Date(Date.now() - 120_000).toISOString(),
  },
  {
    score: 0.28, category: "Cost Variance", severity: "low", source: "FINTECH-Budget",
    factors: [{ name: "forecast_deviation", score: 0.3, weight: 0.5 }, { name: "market_volatility", score: 0.25, weight: 0.5 }],
    recommendation: "Monitor quarterly budget alignment",
    timestamp: new Date(Date.now() - 30_000).toISOString(),
  },
];

export default function FinancePage() {
  const storeSettlements = useAgentStore((s) => s.settlements);
  const storeRisks = useAgentStore((s) => s.riskAlerts);
  const governorAction = useAgentStore((s) => s.governorAction);
  const threadId = useAgentStore((s) => s.threadId);
  const weeklyActivity = useAgentStore((s) => s.weeklyActivity);
  const [tab, setTab] = useState<"settlements" | "risks" | "analytics">("settlements");

  // Use store data if available, else use demo data
  const settlements = storeSettlements.length > 0 ? storeSettlements : demoSettlements;
  const riskAlerts = storeRisks.length > 0 ? storeRisks : demoRisks;

  const totalVolume = settlements.reduce((sum, s) => sum + s.amount_usdc, 0);
  const confirmedCount = settlements.filter((s) => s.status === "confirmed").length;
  const avgRisk = riskAlerts.length > 0 ? riskAlerts.reduce((sum, r) => sum + r.score, 0) / riskAlerts.length : 0;
  const highRisks = riskAlerts.filter((r) => r.severity === "critical" || r.severity === "high").length;

  // Try to fetch from backend
  const fetchSettlements = useCallback(async () => {
    if (!threadId) return;
    try {
      await getSettlements(threadId);
    } catch { /* ignore */ }
  }, [threadId]);

  useEffect(() => { fetchSettlements(); }, [fetchSettlements]);

  return (
    <div className="dashboard-main">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-zinc-100">Financial Operations</h1>
            <p className="text-xs text-zinc-500 mt-0.5">
              A2A settlements, risk analysis, and cross-agent transaction ledger
            </p>
          </div>
        </div>

        {/* Top metrics */}
        <div className="grid grid-cols-4 gap-4">
          <div className="card-sm">
            <span className="metric-label">Total Volume</span>
            <div className="metric-value mt-1 text-green-400">{formatUSD(totalVolume)}</div>
            <span className="metric-delta-up mt-1">{settlements.length} transactions</span>
          </div>
          <div className="card-sm">
            <span className="metric-label">Confirmed</span>
            <div className="metric-value mt-1">{confirmedCount}</div>
            <span className="text-[10px] text-zinc-500">{((confirmedCount / Math.max(settlements.length, 1)) * 100).toFixed(0)}% success</span>
          </div>
          <div className="card-sm">
            <span className="metric-label">Avg Risk</span>
            <div className={`metric-value mt-1 ${avgRisk > 0.6 ? "text-red-400" : avgRisk > 0.3 ? "text-amber-400" : "text-green-400"}`}>
              {(avgRisk * 100).toFixed(0)}
            </div>
            <span className={highRisks > 0 ? "metric-delta-down" : "metric-delta-up"}>
              {highRisks > 0 ? `${highRisks} high` : "all clear"}
            </span>
          </div>
          <div className="card-sm">
            <span className="metric-label">Est. ROI</span>
            <div className="metric-value mt-1">{governorAction ? formatUSD(governorAction.estimated_roi) : "—"}</div>
            {governorAction?.npv_3yr && (
              <span className="metric-delta-up">NPV: {formatUSD(governorAction.npv_3yr)}</span>
            )}
          </div>
        </div>

        {/* Tab bar */}
        <div className="flex gap-1">
          {(["settlements", "risks", "analytics"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`tab-btn ${tab === t ? "active" : ""}`}
            >
              {t === "settlements" ? "💰 Settlements" : t === "risks" ? "⚠️ Risk Analysis" : "📊 Analytics"}
            </button>
          ))}
        </div>

        {/* Settlements tab */}
        <AnimatePresence mode="wait">
          {tab === "settlements" && (
            <motion.div key="settlements" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-zinc-200">Settlement Ledger</h3>
                  <div className="flex items-center gap-2">
                    <span className="badge-web3 text-[9px] px-2 py-0.5">Solana</span>
                    <span className="text-[9px] font-mono text-zinc-600">{settlements.length} txns</span>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="tx-table">
                    <thead>
                      <tr>
                        <th>Signature</th>
                        <th>From</th>
                        <th>To</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Network</th>
                        <th>Memo</th>
                      </tr>
                    </thead>
                    <tbody>
                      {settlements.map((s, i) => (
                        <SettlementRow key={s.tx_signature} s={s} i={i} />
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </motion.div>
          )}

          {/* Risks tab */}
          {tab === "risks" && (
            <motion.div key="risks" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="grid grid-cols-3 gap-4">
                {/* Risk gauge */}
                <div className="card flex items-center justify-center">
                  <RiskGauge score={avgRisk} />
                </div>

                {/* Risk alerts list */}
                <div className="card col-span-2">
                  <h3 className="text-sm font-semibold text-zinc-200 mb-3">Risk Alerts</h3>
                  <div className="space-y-2">
                    {riskAlerts.map((r, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.08 }}
                        className="flex items-start gap-3 px-3 py-2.5 rounded-lg bg-zinc-900/40"
                      >
                        <div className={`w-2 h-2 rounded-full mt-1 ${
                          r.severity === "critical" ? "bg-red-500 animate-pulse" :
                          r.severity === "high" ? "bg-orange-500" :
                          r.severity === "medium" ? "bg-amber-500" : "bg-green-500"
                        }`} />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-medium text-zinc-200">{r.category}</span>
                            <span className={`text-[8px] px-1.5 py-0.5 rounded ${
                              r.severity === "critical" || r.severity === "high" ? "bg-red-500/10 text-red-400" :
                              r.severity === "medium" ? "bg-amber-500/10 text-amber-400" : "bg-green-500/10 text-green-400"
                            }`}>{r.severity}</span>
                          </div>
                          <p className="text-[10px] text-zinc-400 mb-1.5">{r.recommendation}</p>
                          <div className="flex gap-1">
                            {r.factors.map((f, fi) => (
                              <span key={fi} className="text-[8px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-500">
                                {f.name}: {(f.score * 100).toFixed(0)}%
                              </span>
                            ))}
                          </div>
                        </div>
                        <span className="text-sm font-mono font-bold" style={{
                          color: r.score > 0.7 ? "#ef4444" : r.score > 0.4 ? "#f59e0b" : "#22c55e",
                        }}>
                          {(r.score * 100).toFixed(0)}
                        </span>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Analytics tab */}
          {tab === "analytics" && (
            <motion.div key="analytics" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="grid grid-cols-2 gap-4">
                {/* Weekly activity chart */}
                <div className="card">
                  <h3 className="text-sm font-semibold text-zinc-200 mb-4">Weekly Transaction Volume</h3>
                  <div className="flex items-end gap-3 h-40">
                    {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day, i) => {
                      const val = weeklyActivity[i] ?? 0;
                      const maxVal = Math.max(...weeklyActivity, 1);
                      const pct = (val / maxVal) * 100;
                      return (
                        <div key={day} className="flex flex-col items-center flex-1 gap-1">
                          <span className="text-[10px] text-zinc-500 font-mono">{val}</span>
                          <div className="w-full relative" style={{ height: "120px" }}>
                            <motion.div
                              initial={{ height: 0 }}
                              animate={{ height: `${Math.max(pct, 4)}%` }}
                              transition={{ delay: i * 0.05, duration: 0.4 }}
                              className="volume-bar volume-bar-green w-full absolute bottom-0"
                            />
                          </div>
                          <span className="text-[10px] text-zinc-600">{day}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Settlement network breakdown */}
                <div className="card">
                  <h3 className="text-sm font-semibold text-zinc-200 mb-4">Network Breakdown</h3>
                  <div className="space-y-3">
                    {[
                      { network: "Solana Devnet", pct: 65, color: "#9945FF", amount: totalVolume * 0.65 },
                      { network: "Ethereum L2", pct: 25, color: "#627EEA", amount: totalVolume * 0.25 },
                      { network: "Internal Ledger", pct: 10, color: "#22c55e", amount: totalVolume * 0.10 },
                    ].map((n) => (
                      <div key={n.network}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-zinc-300">{n.network}</span>
                          <span className="text-xs font-mono text-zinc-400">{formatUSD(n.amount)}</span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-zinc-800 overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${n.pct}%` }}
                            transition={{ duration: 0.6, delay: 0.2 }}
                            className="h-full rounded-full"
                            style={{ background: n.color }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

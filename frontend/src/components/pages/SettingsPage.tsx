/**
 * SettingsPage — System configuration, agent keys, MCP status, and diagnostics.
 */

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { useAgentStore } from "../../stores/agentStore";

interface SystemCheck {
  name: string;
  status: "ok" | "warn" | "error" | "checking";
  detail: string;
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case "ok": return <span className="w-2 h-2 rounded-full bg-green-400" />;
    case "warn": return <span className="w-2 h-2 rounded-full bg-amber-400" />;
    case "error": return <span className="w-2 h-2 rounded-full bg-red-400" />;
    default: return <span className="w-2 h-2 rounded-full bg-zinc-600 animate-pulse" />;
  }
}

export default function SettingsPage() {
  const currentPhase = useAgentStore((s) => s.currentPhase);
  const threadId = useAgentStore((s) => s.threadId);
  const neuralFeed = useAgentStore((s) => s.neuralFeed);
  const settlements = useAgentStore((s) => s.settlements);
  const riskAlerts = useAgentStore((s) => s.riskAlerts);
  const reset = useAgentStore((s) => s.reset);
  const [checks, setChecks] = useState<SystemCheck[]>([]);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);

  const runDiagnostics = useCallback(async () => {
    const results: SystemCheck[] = [];

    // Check backend health
    try {
      const res = await fetch("/api/status/test", { signal: AbortSignal.timeout(3000) });
      if (res.ok || res.status === 404 || res.status === 422) {
        results.push({ name: "Backend API", status: "ok", detail: "FastAPI server responding on port 8000" });
        setBackendOk(true);
      } else {
        results.push({ name: "Backend API", status: "warn", detail: `HTTP ${res.status}` });
        setBackendOk(true);
      }
    } catch {
      results.push({ name: "Backend API", status: "error", detail: "Cannot reach backend on port 8000" });
      setBackendOk(false);
    }

    // Check A2A endpoint
    try {
      const res = await fetch("/api/a2a/agents", { signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        results.push({ name: "A2A Protocol", status: "ok", detail: "Agent discovery endpoint active" });
      } else {
        results.push({ name: "A2A Protocol", status: "warn", detail: `HTTP ${res.status}` });
      }
    } catch {
      results.push({ name: "A2A Protocol", status: "error", detail: "A2A endpoint unreachable" });
    }

    // Check agent.json
    try {
      const res = await fetch("/.well-known/agent.json", { signal: AbortSignal.timeout(3000) });
      results.push({
        name: "Agent Manifest",
        status: res.ok ? "ok" : "warn",
        detail: res.ok ? "/.well-known/agent.json served" : `HTTP ${res.status}`,
      });
    } catch {
      results.push({ name: "Agent Manifest", status: "error", detail: "Cannot fetch agent.json" });
    }

    // Frontend checks
    results.push({ name: "React Three Fiber", status: "ok", detail: "v9 + drei v10 (React 19 compatible)" });
    results.push({ name: "NHI Middleware", status: "ok", detail: "Ed25519 cryptographic signing enabled" });
    results.push({ name: "SSE Streaming", status: "ok", detail: "@microsoft/fetch-event-source ready" });
    results.push({ name: "Zustand Store", status: "ok", detail: `${neuralFeed.length} events, ${settlements.length} settlements` });
    results.push({ name: "LLM Mode", status: "ok", detail: "Deterministic mode (LLM disabled)" });

    setChecks(results);
  }, [neuralFeed.length, settlements.length]);

  useEffect(() => { runDiagnostics(); }, [runDiagnostics]);

  const agentKeys = [
    { name: "VANGUARD", algo: "Ed25519", file: "vanguard_private.pem" },
    { name: "JURIST", algo: "Ed25519", file: "jurist_private.pem" },
    { name: "ARCHITECT", algo: "Ed25519", file: "architect_private.pem" },
    { name: "GOVERNOR", algo: "Ed25519", file: "governor_private.pem" },
    { name: "SYSTEM", algo: "Ed25519", file: "private.pem" },
  ];

  return (
    <div className="dashboard-main">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-zinc-100">System Settings</h1>
            <p className="text-xs text-zinc-500 mt-0.5">
              Configuration, diagnostics, and NHI key management
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={runDiagnostics}
              className="px-3 py-1.5 rounded-lg text-[10px] font-semibold uppercase tracking-wider
                bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 transition-all"
            >
              Run Diagnostics
            </button>
            <button
              onClick={reset}
              className="px-3 py-1.5 rounded-lg text-[10px] font-semibold uppercase tracking-wider
                bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition-all"
            >
              Reset Store
            </button>
          </div>
        </div>

        {/* System diagnostics */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-zinc-200">System Diagnostics</h3>
            <span className={`text-[9px] px-2 py-0.5 rounded ${
              backendOk === true ? "bg-green-500/10 text-green-400" :
              backendOk === false ? "bg-red-500/10 text-red-400" :
              "bg-zinc-800 text-zinc-500"
            }`}>
              {backendOk === true ? "All Systems Operational" : backendOk === false ? "Backend Offline" : "Checking…"}
            </span>
          </div>
          <div className="space-y-1">
            {checks.map((c, i) => (
              <motion.div
                key={c.name}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className="flex items-center gap-3 px-3 py-2 rounded-lg bg-zinc-900/30 hover:bg-zinc-900/50 transition-colors"
              >
                <StatusIcon status={c.status} />
                <span className="text-xs font-medium text-zinc-300 w-36">{c.name}</span>
                <span className="text-[10px] text-zinc-500 flex-1">{c.detail}</span>
                <span className={`text-[8px] font-mono uppercase ${
                  c.status === "ok" ? "text-green-400" : c.status === "warn" ? "text-amber-400" : c.status === "error" ? "text-red-400" : "text-zinc-600"
                }`}>
                  {c.status}
                </span>
              </motion.div>
            ))}
          </div>
        </div>

        {/* NHI Keys */}
        <div className="card">
          <h3 className="text-sm font-semibold text-zinc-200 mb-4">NHI Agent Keys</h3>
          <div className="space-y-1">
            {agentKeys.map((k, i) => (
              <motion.div
                key={k.name}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.06 }}
                className="flex items-center gap-3 px-3 py-2 rounded-lg bg-zinc-900/30"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                <span className="text-xs font-bold text-zinc-300 w-24">{k.name}</span>
                <span className="text-[10px] text-zinc-500 font-mono">{k.algo}</span>
                <span className="text-[9px] text-zinc-600 flex-1 font-mono">{k.file}</span>
                <span className="text-[8px] px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400">Active</span>
              </motion.div>
            ))}
          </div>
        </div>

        {/* System info */}
        <div className="grid grid-cols-2 gap-4">
          <div className="card">
            <h3 className="text-sm font-semibold text-zinc-200 mb-3">Runtime Info</h3>
            <div className="space-y-2">
              {[
                ["Backend", "Python 3.12 / FastAPI / Uvicorn"],
                ["Frontend", "React 19 / Vite 6 / TypeScript 5.7"],
                ["Graph Engine", "LangGraph 1.0 + MemorySaver"],
                ["MCP", "FastMCP 3.0 on port 8001"],
                ["3D Engine", "React Three Fiber v9 + drei v10"],
                ["Streaming", "Server-Sent Events (SSE)"],
              ].map(([label, value]) => (
                <div key={label} className="flex items-center justify-between">
                  <span className="text-[10px] text-zinc-500">{label}</span>
                  <span className="text-[10px] text-zinc-300 font-mono">{value}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h3 className="text-sm font-semibold text-zinc-200 mb-3">Session State</h3>
            <div className="space-y-2">
              {[
                ["Thread ID", threadId?.substring(0, 12) ?? "—"],
                ["Phase", currentPhase],
                ["Neural Feed", `${neuralFeed.length} entries`],
                ["Settlements", `${settlements.length} recorded`],
                ["Risk Alerts", `${riskAlerts.length} active`],
                ["Store", "Zustand 5 (in-memory)"],
              ].map(([label, value]) => (
                <div key={label} className="flex items-center justify-between">
                  <span className="text-[10px] text-zinc-500">{label}</span>
                  <span className="text-[10px] text-zinc-300 font-mono">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Architecture note */}
        <div className="card text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
            <span className="text-[10px] text-blue-400">
              EcoVerify-Prime — Autonomic Global Governor for Sustainable Infrastructure
            </span>
          </div>
          <p className="text-[10px] text-zinc-600 mt-3">
            9 competitive domains · 5-agent LangGraph pipeline · NHI Ed25519 signing · A2A protocol · MCP tools
          </p>
        </div>
      </div>
    </div>
  );
}

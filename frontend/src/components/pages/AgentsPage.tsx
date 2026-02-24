/**
 * AgentsPage — Shows all agents in the EcoVerify-Prime pipeline,
 * their NHI signing status, capabilities, and communication grid.
 */

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { useAgentStore } from "../../stores/agentStore";
import { getAgentCards } from "../../lib/api";

interface AgentDef {
  key: string;
  name: string;
  role: string;
  description: string;
  color: string;
  badge: string;
  capabilities: string[];
  icon: string;
}

const agents: AgentDef[] = [
  {
    key: "vanguard",
    name: "VANGUARD",
    role: "Anomaly Detector",
    description: "BMS telemetry ingestion & anomaly detection via Monte Carlo simulation. First responder in the agent pipeline.",
    color: "#3b82f6",
    badge: "badge-vanguard",
    capabilities: ["BMS Integration", "Monte Carlo", "Anomaly Scoring", "Energy Telemetry"],
    icon: "🔍",
  },
  {
    key: "jurist",
    name: "JURIST",
    role: "Regulatory Analyst",
    description: "EU AI Act compliance verification with citation checking. Self-corrects on hallucinated citations.",
    color: "#a855f7",
    badge: "badge-jurist",
    capabilities: ["EU AI Act", "Citation Verification", "Self-Correction", "Regulatory Corpus"],
    icon: "⚖️",
  },
  {
    key: "architect",
    name: "ARCHITECT",
    role: "Solution Engineer",
    description: "Generates actionable remediation plans with ROI analysis, NPV calculations, and payback estimates.",
    color: "#10b981",
    badge: "badge-architect",
    capabilities: ["ROI Analysis", "NPV Modeling", "Remediation Plans", "Cost Optimization"],
    icon: "🏗️",
  },
  {
    key: "governor",
    name: "GOVERNOR",
    role: "HITL Gatekeeper",
    description: "Human-in-the-loop approval checkpoint. Reviews proposals, adjusts ROI factors, and gates execution.",
    color: "#f59e0b",
    badge: "badge-governor",
    capabilities: ["HITL Approval", "ROI Adjustment", "Risk Gating", "Executive Override"],
    icon: "🛡️",
  },
  {
    key: "finalize",
    name: "FINALIZE",
    role: "Settlement Engine",
    description: "Executes approved actions, records settlements, and generates cryptographic decision traces.",
    color: "#06b6d4",
    badge: "badge-system",
    capabilities: ["Settlement Execution", "NHI Signing", "Trace Generation", "A2A Settlement"],
    icon: "✅",
  },
];

const pipelineSteps = ["VANGUARD", "JURIST", "ARCHITECT", "GOVERNOR", "FINALIZE"];

function AgentCard({ agent, isActive, phaseIndex }: { agent: AgentDef; isActive: boolean; phaseIndex: number }) {
  const agentIndex = pipelineSteps.indexOf(agent.name);
  const isPast = phaseIndex > agentIndex;
  const isCurrent = phaseIndex === agentIndex;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: agentIndex * 0.08 }}
      className={`card-sm relative overflow-hidden transition-all duration-300 ${
        isCurrent ? "ring-1" : ""
      }`}
      style={{
        borderColor: isCurrent ? agent.color : undefined,
        boxShadow: isCurrent ? `0 0 20px ${agent.color}20` : undefined,
      }}
    >
      {/* Status indicator */}
      <div className="absolute top-3 right-3 flex items-center gap-1.5">
        <span className={`text-[8px] font-mono uppercase tracking-wider ${
          isPast ? "text-green-400" : isCurrent ? "text-amber-400 animate-pulse" : "text-zinc-600"
        }`}>
          {isPast ? "COMPLETE" : isCurrent ? "ACTIVE" : "STANDBY"}
        </span>
        <div className={`w-2 h-2 rounded-full ${
          isPast ? "bg-green-400" : isCurrent ? "bg-amber-400 animate-pulse-glow" : "bg-zinc-700"
        }`} />
      </div>

      {/* Header */}
      <div className="flex items-center gap-3 mb-3">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center text-lg"
          style={{ background: `${agent.color}15`, border: `1px solid ${agent.color}30` }}
        >
          {agent.icon}
        </div>
        <div>
          <h3 className="text-sm font-bold text-zinc-200">{agent.name}</h3>
          <p className="text-[10px] text-zinc-500">{agent.role}</p>
        </div>
      </div>

      {/* Description */}
      <p className="text-[11px] text-zinc-400 leading-relaxed mb-3">
        {agent.description}
      </p>

      {/* Capabilities */}
      <div className="flex flex-wrap gap-1.5">
        {agent.capabilities.map((cap) => (
          <span
            key={cap}
            className="text-[9px] px-2 py-0.5 rounded-full font-medium"
            style={{
              background: `${agent.color}10`,
              color: agent.color,
              border: `1px solid ${agent.color}20`,
            }}
          >
            {cap}
          </span>
        ))}
      </div>

      {/* NHI Signing status */}
      <div className="mt-3 pt-3 border-t border-zinc-800/50 flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
        <span className="text-[9px] text-purple-400 font-mono">Ed25519 NHI-signed</span>
      </div>
    </motion.div>
  );
}

function getPipelineIndex(phase: string): number {
  const map: Record<string, number> = {
    vanguard_complete: 0,
    jurist_complete: 1,
    citation_failure: 1,
    architect_complete: 2,
    interrupted: 3,
    governor_approved: 3,
    governor_rejected: 3,
    complete: 4,
  };
  if (phase === "starting") return 0;
  return map[phase] ?? -1;
}

export default function AgentsPage() {
  const currentPhase = useAgentStore((s) => s.currentPhase);
  const neuralFeed = useAgentStore((s) => s.neuralFeed);
  const decisionTraces = useAgentStore((s) => s.decisionTraces);
  const [a2aAgents, setA2aAgents] = useState<Array<{ name: string; description: string; capabilities: string[]; url: string }>>([]);
  const phaseIndex = getPipelineIndex(currentPhase);

  const loadA2A = useCallback(async () => {
    try {
      const { agents } = await getAgentCards();
      setA2aAgents(agents);
    } catch {
      // Backend might not be running
    }
  }, []);

  useEffect(() => { loadA2A(); }, [loadA2A]);

  // Agent message counts
  const agentMessages = (name: string) =>
    neuralFeed.filter((e) => e.agent === name).length;

  return (
    <div className="dashboard-main">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-zinc-100">Agent Pipeline</h1>
            <p className="text-xs text-zinc-500 mt-0.5">
              5-node LangGraph orchestration with NHI cryptographic signing
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[9px] font-mono text-zinc-600 uppercase">
              Phase: {currentPhase}
            </span>
            <div className={`status-dot ${currentPhase !== "idle" ? "status-dot-live" : "status-dot-idle"}`} />
          </div>
        </div>

        {/* Pipeline visualization */}
        <div className="card">
          <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-4">
            Execution Pipeline
          </h3>
          <div className="flex items-center justify-between px-4">
            {pipelineSteps.map((step, i) => {
              const agent = agents[i];
              const isPast = phaseIndex > i;
              const isCurrent = phaseIndex === i;
              return (
                <div key={step} className="flex items-center">
                  {i > 0 && (
                    <div className="w-12 h-px mx-2" style={{
                      background: isPast ? agent.color : "rgba(255,255,255,0.06)",
                    }} />
                  )}
                  <motion.div
                    animate={isCurrent ? { scale: [1, 1.15, 1] } : {}}
                    transition={isCurrent ? { repeat: Infinity, duration: 1.5 } : {}}
                    className="flex flex-col items-center gap-1"
                  >
                    <div
                      className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all"
                      style={{
                        background: isPast || isCurrent ? `${agent.color}20` : "rgba(255,255,255,0.03)",
                        border: `2px solid ${isPast || isCurrent ? agent.color : "rgba(255,255,255,0.06)"}`,
                        color: isPast || isCurrent ? agent.color : "rgba(255,255,255,0.15)",
                        boxShadow: isCurrent ? `0 0 12px ${agent.color}30` : "none",
                      }}
                    >
                      {isPast ? "✓" : agent.icon}
                    </div>
                    <span className="text-[9px] font-mono" style={{
                      color: isPast || isCurrent ? agent.color : "var(--color-zinc-600)",
                    }}>
                      {step}
                    </span>
                    <span className="text-[8px] text-zinc-600">
                      {agentMessages(step)} msgs
                    </span>
                  </motion.div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Agent cards grid */}
        <div className="grid grid-cols-2 gap-4">
          {agents.map((agent) => (
            <AgentCard key={agent.key} agent={agent} isActive={phaseIndex === pipelineSteps.indexOf(agent.name)} phaseIndex={phaseIndex} />
          ))}

          {/* A2A Discovery card */}
          <div className="card-sm">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-lg">
                🌐
              </div>
              <div>
                <h3 className="text-sm font-bold text-zinc-200">A2A Protocol</h3>
                <p className="text-[10px] text-zinc-500">Agent-to-Agent Discovery</p>
              </div>
            </div>
            <p className="text-[11px] text-zinc-400 leading-relaxed mb-3">
              Google A2A-compatible agent discovery via /.well-known/agent.json endpoint.
            </p>
            {a2aAgents.length > 0 ? (
              <div className="space-y-1.5">
                {a2aAgents.map((a, i) => (
                  <div key={i} className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-zinc-900/40">
                    <span className="text-[10px] text-cyan-400 font-medium">{a.name}</span>
                    <span className="text-[9px] text-zinc-600 flex-1 truncate">{a.description}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-3">
                <span className="text-[10px] text-zinc-600 italic">Connect backend to discover agents</span>
              </div>
            )}
          </div>
        </div>

        {/* Decision traces */}
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
              NHI Decision Traces
            </h3>
            <span className="text-[9px] font-mono text-zinc-600">{decisionTraces.length} traces</span>
          </div>
          {decisionTraces.length === 0 ? (
            <p className="text-[10px] text-zinc-600 text-center py-6 italic">
              Run the pipeline to generate cryptographically signed decision traces
            </p>
          ) : (
            <div className="space-y-1.5 max-h-60 overflow-y-auto">
              {decisionTraces.map((t, i) => (
                <div key={i} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-zinc-900/40">
                  <span className="text-[9px] font-bold text-zinc-500 w-20">{t.agent_id}</span>
                  <span className="text-[10px] text-zinc-400 flex-1 truncate font-mono">
                    {t.payload_hash.slice(0, 32)}…
                  </span>
                  <span className={`text-[8px] font-mono ${t.verified ? "text-green-400" : "text-red-400"}`}>
                    {t.verified ? "✓ VERIFIED" : "✗ UNVERIFIED"}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

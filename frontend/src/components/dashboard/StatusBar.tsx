/**
 * StatusBar — Finance Report style top bar with agent pipeline, live clock, and demo trigger.
 */

import { useCallback, useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useAgentStore } from "../../stores/agentStore";
import { useAgentStream } from "../../hooks/useAgentStream";
import { startRun, injectAnomaly, startDemo } from "../../lib/api";

const phaseLabels: Record<string, string> = {
  idle: "STANDING BY",
  starting: "INITIALIZING",
  vanguard_complete: "VANGUARD ✓",
  jurist_complete: "JURIST ✓",
  architect_complete: "ARCHITECT ✓",
  governor_approved: "APPROVED",
  governor_rejected: "REJECTED",
  interrupted: "AWAITING APPROVAL",
  complete: "COMPLETE",
  citation_failure: "SELF-CORRECTING",
  error: "ERROR",
};

const pipeline = [
  { key: "vanguard", label: "VGD", color: "#3b82f6", phases: ["vanguard_complete"] },
  { key: "jurist", label: "JUR", color: "#a855f7", phases: ["jurist_complete", "citation_failure"] },
  { key: "architect", label: "ARC", color: "#10b981", phases: ["architect_complete"] },
  { key: "governor", label: "GOV", color: "#f59e0b", phases: ["interrupted", "governor_approved", "governor_rejected"] },
  { key: "finalize", label: "FIN", color: "#06b6d4", phases: ["complete"] },
];

function getPipelineStage(phase: string): number {
  for (let i = 0; i < pipeline.length; i++) {
    if (pipeline[i].phases.includes(phase)) return i;
  }
  if (phase === "starting") return -1;
  return -2;
}

function useLiveClock() {
  const [time, setTime] = useState(() =>
    new Date().toLocaleTimeString("en-US", { hour12: false })
  );
  useEffect(() => {
    const id = setInterval(() => {
      setTime(new Date().toLocaleTimeString("en-US", { hour12: false }));
    }, 1000);
    return () => clearInterval(id);
  }, []);
  return time;
}

export default function StatusBar() {
  const currentPhase = useAgentStore((s) => s.currentPhase);
  const isRunning = useAgentStore((s) => s.isRunning);
  const threadId = useAgentStore((s) => s.threadId);
  const reset = useAgentStore((s) => s.reset);
  const { connect, connectDemo } = useAgentStream();
  const [isTriggering, setIsTriggering] = useState(false);
  const [isDemoRunning, setIsDemoRunning] = useState(false);
  const pipelineStage = getPipelineStage(currentPhase);
  const clock = useLiveClock();

  const handleTriggerAnomaly = useCallback(async () => {
    if (isTriggering) return;
    setIsTriggering(true);
    try {
      reset();
      await injectAnomaly("HQ-01", 0.7);
      const { thread_id } = await startRun("HQ-01");
      connect(thread_id);
    } catch (e) {
      console.error("[StatusBar] Trigger failed:", e);
      const { addFeedEntry } = useAgentStore.getState();
      addFeedEntry({
        id: `err-${Date.now()}`,
        agent: "SYSTEM",
        message: `Connection error: ${e instanceof Error ? e.message : "Backend unreachable"}. Ensure backend is running on port 8000.`,
        severity: "high",
        timestamp: new Date().toISOString(),
        feedType: "neural_feed",
      });
    } finally {
      setIsTriggering(false);
    }
  }, [isTriggering, reset, connect]);

  const handleDemo = useCallback(async () => {
    if (isDemoRunning || isRunning) return;
    setIsDemoRunning(true);
    try {
      reset();
      await startDemo();
      connectDemo();
    } catch (e) {
      console.error("[StatusBar] Demo failed:", e);
      const { addFeedEntry } = useAgentStore.getState();
      addFeedEntry({
        id: `err-${Date.now()}`,
        agent: "SYSTEM",
        message: `Demo error: ${e instanceof Error ? e.message : "Backend unreachable"}`,
        severity: "high",
        timestamp: new Date().toISOString(),
        feedType: "neural_feed",
      });
    } finally {
      setIsDemoRunning(false);
    }
  }, [isDemoRunning, isRunning, reset, connectDemo]);

  return (
    <div className="top-bar dashboard-top">
      {/* Branding */}
      <div className="flex items-center gap-2.5 min-w-[160px]">
        <span className="text-sm font-bold tracking-wide text-zinc-100">
          EcoVerify<span className="text-blue-400">-Prime</span>
        </span>
        <div className={`status-dot ${isRunning ? "status-dot-live" : "status-dot-idle"}`} />
      </div>

      {/* Pipeline chips */}
      <div className="flex items-center gap-1 ml-6">
        {pipeline.map((stage, i) => {
          const isActive = pipelineStage === i;
          const isPast = pipelineStage > i;
          return (
            <div key={stage.key} className="flex items-center">
              {i > 0 && (
                <div
                  className="w-4 h-px mx-0.5 transition-all duration-300"
                  style={{
                    background: isPast ? stage.color : "rgba(255,255,255,0.06)",
                  }}
                />
              )}
              <motion.div
                animate={isActive ? { scale: [1, 1.1, 1] } : { scale: 1 }}
                transition={isActive ? { duration: 1.5, repeat: Infinity } : {}}
                className="flex items-center justify-center w-7 h-6 rounded-md text-[8px] font-bold tracking-wider transition-all duration-300"
                style={{
                  background:
                    isActive || isPast
                      ? `${stage.color}18`
                      : "rgba(255,255,255,0.02)",
                  border: `1px solid ${
                    isActive || isPast
                      ? `${stage.color}35`
                      : "rgba(255,255,255,0.04)"
                  }`,
                  color:
                    isActive || isPast ? stage.color : "rgba(255,255,255,0.15)",
                  boxShadow: isActive
                    ? `0 0 8px ${stage.color}20`
                    : "none",
                }}
              >
                {stage.label}
              </motion.div>
            </div>
          );
        })}
      </div>

      {/* Phase label */}
      <span className="ml-4 text-[10px] font-mono text-zinc-500 uppercase tracking-widest">
        {phaseLabels[currentPhase] ?? currentPhase.toUpperCase()}
      </span>

      {/* Thread ID */}
      {threadId && (
        <span className="ml-3 text-[9px] font-mono text-zinc-600 bg-zinc-900 px-2 py-0.5 rounded">
          {threadId.substring(0, 8)}
        </span>
      )}

      <div className="flex-1" />

      {/* Live clock */}
      <span className="text-[11px] font-mono text-zinc-500 mr-5 tabular-nums">
        {clock}
      </span>

      {/* Trigger */}
      <motion.button
        onClick={handleDemo}
        disabled={isDemoRunning || isRunning || isTriggering}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className={`px-4 py-1.5 rounded-lg text-[10px] font-semibold uppercase tracking-wider
          transition-all duration-200 mr-2
          ${
            isDemoRunning || isRunning
              ? "bg-zinc-900 text-zinc-600 cursor-not-allowed border border-zinc-800"
              : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20"
          }`}
      >
        {isDemoRunning ? "Demo…" : "▶ Demo"}
      </motion.button>
      <motion.button
        onClick={handleTriggerAnomaly}
        disabled={isTriggering || isRunning}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className={`px-4 py-1.5 rounded-lg text-[10px] font-semibold uppercase tracking-wider
          transition-all duration-200
          ${
            isTriggering || isRunning
              ? "bg-zinc-900 text-zinc-600 cursor-not-allowed border border-zinc-800"
              : "bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20"
          }`}
      >
        {isTriggering ? "Triggering…" : isRunning ? "Running…" : " Trigger"}
      </motion.button>
    </div>
  );
}

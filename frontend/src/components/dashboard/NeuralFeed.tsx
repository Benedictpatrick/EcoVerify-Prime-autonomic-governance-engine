/**
 * NeuralFeed — compact real-time agent thought-stream.
 * Fits in the main grid. Supports new domain agents and feed types.
 */

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAgentStore } from "../../stores/agentStore";
import type { AgentName, NeuralFeedEntry } from "../../lib/types";

const badgeClass: Record<AgentName, string> = {
  VANGUARD: "badge-vanguard",
  JURIST: "badge-jurist",
  ARCHITECT: "badge-architect",
  GOVERNOR: "badge-governor",
  SYSTEM: "badge-system",
  FHIR: "badge-health",
  FINTECH: "badge-fintech",
  EDUTECH: "badge-edutech",
};

const severityDot: Record<string, string> = {
  critical: "bg-red-500 animate-pulse-glow",
  high: "bg-red-500",
  medium: "bg-amber-500",
  low: "bg-emerald-500/60",
};

function FeedEntry({ entry }: { entry: NeuralFeedEntry }) {
  const time = new Date(entry.timestamp).toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -10 }}
      transition={{ duration: 0.12, ease: "easeOut" }}
      className="flex items-start gap-2 py-2 px-2 rounded-lg hover:bg-white/[0.02] transition-colors"
    >
      <div
        className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${
          severityDot[entry.severity] ?? "bg-zinc-600"
        }`}
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 mb-0.5">
          <span
            className={`text-[8px] font-bold uppercase tracking-wider px-1 py-[1px] rounded ${
              badgeClass[entry.agent] ?? "badge-system"
            }`}
          >
            {entry.agent}
          </span>
          <span className="text-[8px] text-zinc-600 font-mono">{time}</span>
        </div>
        <p className="text-[11px] text-zinc-400 leading-snug truncate">
          {entry.message}
        </p>
      </div>
    </motion.div>
  );
}

export default function NeuralFeed() {
  const feed = useAgentStore((s) => s.neuralFeed);
  const isRunning = useAgentStore((s) => s.isRunning);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [feed.length]);

  return (
    <div className="card flex flex-col h-full max-h-[400px] animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-2 pb-3 border-b border-zinc-800/60 mb-2">
        <div
          className={`status-dot ${
            isRunning ? "status-dot-live" : "status-dot-idle"
          }`}
        />
        <h3 className="text-xs font-semibold text-zinc-300">Neural Feed</h3>
        <span className="ml-auto text-[9px] font-mono text-zinc-600">
          {feed.length}
        </span>
      </div>

      {/* Feed */}
      <div className="flex-1 overflow-y-auto space-y-0.5">
        <AnimatePresence mode="popLayout">
          {feed.map((entry) => (
            <FeedEntry key={entry.id} entry={entry} />
          ))}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>

      {feed.length === 0 && (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-[10px] text-zinc-600 italic">
            Awaiting agent activity…
          </p>
        </div>
      )}
    </div>
  );
}

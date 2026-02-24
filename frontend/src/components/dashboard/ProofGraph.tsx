/**
 * ProofGraph — tabbed card showing Reasoning (Mermaid), Traces, and Signatures.
 * Sits in the main grid as a collapsible card.
 */

import { useEffect, useRef, useCallback, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import mermaid from "mermaid";
import { useAgentStore } from "../../stores/agentStore";
import type { NeuralFeedEntry } from "../../lib/types";

mermaid.initialize({
  startOnLoad: false,
  theme: "dark",
  themeVariables: {
    primaryColor: "#1e40af",
    primaryTextColor: "#d4d4d8",
    primaryBorderColor: "#3b82f6",
    lineColor: "#3f3f46",
    secondaryColor: "#6b21a8",
    tertiaryColor: "#065f46",
    background: "#09090b",
    mainBkg: "#18181b",
    nodeBorder: "#27272a",
    clusterBkg: "#0d1117",
    titleColor: "#d4d4d8",
    edgeLabelBackground: "#18181b",
  },
  flowchart: { htmlLabels: true, curve: "basis" },
});

type Tab = "reasoning" | "traces" | "signatures";

export default function ProofGraph() {
  const proofGraph = useAgentStore((s) => s.proofGraph);
  const showProofGraph = useAgentStore((s) => s.showProofGraph);
  const toggleProofGraph = useAgentStore((s) => s.toggleProofGraph);
  const feedEntries = useAgentStore((s) => s.neuralFeed);
  const containerRef = useRef<HTMLDivElement>(null);
  const [tab, setTab] = useState<Tab>("reasoning");

  const renderGraph = useCallback(async () => {
    if (!containerRef.current || !proofGraph) return;
    try {
      const id = `mermaid-${Date.now()}`;
      const { svg } = await mermaid.render(id, proofGraph);
      containerRef.current.innerHTML = svg;
      const svgEl = containerRef.current.querySelector("svg");
      if (svgEl) {
        svgEl.style.maxWidth = "100%";
        svgEl.style.height = "auto";
        svgEl.style.maxHeight = "240px";
      }
    } catch (e) {
      console.warn("[Mermaid] Render error:", e);
      if (containerRef.current) {
        containerRef.current.innerHTML = `<pre class="text-xs text-zinc-500 p-4 font-mono">${proofGraph}</pre>`;
      }
    }
  }, [proofGraph]);

  useEffect(() => {
    if (showProofGraph && proofGraph && tab === "reasoning") {
      renderGraph();
    }
  }, [showProofGraph, proofGraph, renderGraph, tab]);

  // Derive traces and signatures from feed entries
  const traces: NeuralFeedEntry[] = feedEntries
    .filter((e: NeuralFeedEntry) => e.agent !== "SYSTEM")
    .slice(-10)
    .reverse();

  return (
    <div className="span-full animate-fade-in">
      {/* Toggle */}
      <button
        onClick={toggleProofGraph}
        disabled={!proofGraph}
        className={`w-full flex items-center justify-center gap-2 py-2 text-[10px] font-semibold uppercase tracking-widest rounded-t-xl transition-all ${
          proofGraph
            ? "text-zinc-400 hover:text-purple-300 cursor-pointer hover:bg-white/[0.02]"
            : "text-zinc-700 cursor-not-allowed"
        }`}
      >
        <span>{showProofGraph ? "▼" : "▲"}</span>
        <span>Decision Reasoning</span>
        {proofGraph && (
          <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse-glow" />
        )}
      </button>

      {/* Collapsible content */}
      <AnimatePresence>
        {showProofGraph && proofGraph && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="card">
              {/* Tab bar */}
              <div className="flex gap-1 mb-4">
                {(["reasoning", "traces", "signatures"] as Tab[]).map((t) => (
                  <button
                    key={t}
                    onClick={() => setTab(t)}
                    className={`tab-btn ${tab === t ? "active" : ""}`}
                  >
                    {t === "reasoning"
                      ? "⛓ Reasoning"
                      : t === "traces"
                      ? "📋 Traces"
                      : "🔏 Signatures"}
                  </button>
                ))}
              </div>

              {/* Tab content */}
              {tab === "reasoning" && (
                <div
                  ref={containerRef}
                  className="flex items-center justify-center overflow-x-auto min-h-[120px]"
                />
              )}

              {tab === "traces" && (
                <div className="max-h-60 overflow-y-auto space-y-1">
                  {traces.length === 0 && (
                    <p className="text-[10px] text-zinc-600 text-center py-4">
                      No traces recorded
                    </p>
                  )}
                  {traces.map((e: NeuralFeedEntry) => (
                    <div
                      key={e.id}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg bg-zinc-900/40"
                    >
                      <span className="text-[8px] font-bold uppercase tracking-wider text-zinc-500 w-16">
                        {e.agent}
                      </span>
                      <span className="text-[11px] text-zinc-400 flex-1 truncate">
                        {e.message}
                      </span>
                      <span className="text-[9px] font-mono text-zinc-600">
                        {new Date(e.timestamp).toLocaleTimeString("en-US", {
                          hour12: false,
                        })}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {tab === "signatures" && (
                <div className="text-center py-8">
                  <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                    <span className="text-[10px] text-purple-400 font-mono">
                      Ed25519 NHI-signed traces
                    </span>
                  </div>
                  <p className="text-[10px] text-zinc-600 mt-3">
                    All agent decisions cryptographically signed via NHI
                    middleware
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

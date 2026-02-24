import { useAgentStore } from "../../stores/agentStore";
import type { Settlement, EdutechHint } from "../../lib/types";

function SettlementCard({ s }: { s: Settlement }) {
  return (
    <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.04] transition-colors">
      <div className="flex items-center gap-2">
        <span className="text-green-400 text-xs font-mono">$</span>
        <div>
          <p className="text-xs text-zinc-300 font-medium">
            {s.from_agent} → {s.to_agent}
          </p>
          <p className="text-[10px] text-zinc-600">{s.memo}</p>
        </div>
      </div>
      <div className="text-right">
        <p className="text-xs text-zinc-200 font-mono">
          {s.amount_usdc.toFixed(2)} USDC
        </p>
        <p className="text-[10px] text-zinc-600">
          {s.status === "confirmed" ? "✓ confirmed" : s.status}
        </p>
      </div>
    </div>
  );
}

function HintCard({ h }: { h: EdutechHint }) {
  return (
    <div className="flex items-start gap-2 px-3 py-2 rounded-lg bg-white/[0.02]">
      <span className="text-cyan-400 text-xs mt-0.5">📘</span>
      <div>
        <p className="text-xs text-zinc-300 font-medium">{h.topic}</p>
        <p className="text-[10px] text-zinc-500 mt-0.5">{h.content}</p>
        <div className="flex gap-2 mt-1">
          <span className="text-[9px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400">
            {h.urgency}
          </span>
          <span className="text-[9px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400">
            ~{h.estimated_minutes}min
          </span>
        </div>
      </div>
    </div>
  );
}

export default function ActivityPanel() {
  const settlements = useAgentStore((s) => s.settlements);
  const edutechHints = useAgentStore((s) => s.edutechHints);

  return (
    <div className="card span-full animate-fade-in">
      <div className="grid grid-cols-2 gap-6">
        {/* Settlements */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-zinc-200">
              A2A Settlements
            </h3>
            <span className="badge-web3 text-[10px] px-2 py-0.5">
              {settlements.length}
            </span>
          </div>
          <div className="flex flex-col gap-1.5 max-h-40 overflow-y-auto">
            {settlements.length === 0 && (
              <p className="text-xs text-zinc-600 text-center py-4">
                No settlements
              </p>
            )}
            {settlements
              .slice(-5)
              .reverse()
              .map((s: Settlement) => (
                <SettlementCard key={s.tx_signature} s={s} />
              ))}
          </div>
        </div>

        {/* Learning hints */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-zinc-200">
              Learning Engine
            </h3>
            <span className="badge-edutech text-[10px] px-2 py-0.5">
              {edutechHints.length}
            </span>
          </div>
          <div className="flex flex-col gap-1.5 max-h-40 overflow-y-auto">
            {edutechHints.length === 0 && (
              <p className="text-xs text-zinc-600 text-center py-4">
                No recommendations
              </p>
            )}
            {edutechHints
              .slice(-5)
              .reverse()
              .map((h: EdutechHint, i: number) => (
                <HintCard key={i} h={h} />
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}

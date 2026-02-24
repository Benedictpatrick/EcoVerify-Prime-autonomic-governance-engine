import { useAgentStore } from "../../stores/agentStore";
import type { NeuralFeedEntry } from "../../lib/types";

function timeSince(ts: string): string {
  const diff = Date.now() - new Date(ts).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  return `${hrs}h ago`;
}

function severityColor(s: string): string {
  switch (s) {
    case "critical":
      return "text-red-400";
    case "high":
      return "text-orange-400";
    case "medium":
      return "text-amber-400";
    default:
      return "text-zinc-400";
  }
}

function feedIcon(feedType?: string) {
  switch (feedType) {
    case "settlement_update":
      return <span className="text-green-400">$</span>;
    case "risk_alert":
      return <span className="text-red-400">!</span>;
    case "edutech_hint":
      return <span className="text-cyan-400">📘</span>;
    case "fhir_audit":
      return <span className="text-pink-400">♥</span>;
    default:
      return <span className="text-zinc-500">●</span>;
  }
}

export default function RecentEvents() {
  const feedEntries = useAgentStore((s) => s.neuralFeed);

  // Show latest 8
  const recent = feedEntries.slice(-8).reverse();

  return (
    <div className="card animate-fade-in">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-zinc-200">Recent Events</h3>
        <span className="text-[10px] text-zinc-600 font-mono">
          {feedEntries.length} total
        </span>
      </div>

      <div className="flex flex-col gap-2">
        {recent.length === 0 && (
          <p className="text-xs text-zinc-600 text-center py-4">
            No events yet
          </p>
        )}
        {recent.map((entry: NeuralFeedEntry) => (
          <div
            key={entry.id}
            className="flex items-start gap-2 px-2 py-1.5 rounded-lg hover:bg-white/[0.02] transition-colors"
          >
            <div className="mt-0.5 text-xs w-4 text-center">
              {feedIcon(entry.feedType)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-zinc-300 truncate">{entry.message}</p>
              <div className="flex items-center gap-2 mt-0.5">
                <span
                  className={`text-[10px] font-medium ${severityColor(
                    entry.severity
                  )}`}
                >
                  {entry.agent}
                </span>
                <span className="text-[10px] text-zinc-600">
                  {timeSince(entry.timestamp)}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

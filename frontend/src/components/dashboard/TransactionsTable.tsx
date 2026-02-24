import { useAgentStore } from "../../stores/agentStore";
import type { Settlement, RiskAlert } from "../../lib/types";

interface TxRow {
  id: string;
  type: "settlement" | "risk";
  description: string;
  amount: string;
  status: string;
  time: string;
  statusColor: string;
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "—";
  }
}

function buildRows(
  settlements: Settlement[],
  risks: RiskAlert[]
): TxRow[] {
  const sRows: TxRow[] = settlements.map((s) => ({
    id: s.tx_signature.slice(0, 8),
    type: "settlement" as const,
    description: `${s.from_agent} → ${s.to_agent}`,
    amount: `${s.amount_usdc.toFixed(2)} USDC`,
    status: s.status,
    time: formatTime(s.timestamp),
    statusColor:
      s.status === "confirmed" ? "text-green-400" : "text-amber-400",
  }));

  const rRows: TxRow[] = risks.map((r, i) => ({
    id: `risk-${i}`,
    type: "risk" as const,
    description: r.source,
    amount: `score ${r.score.toFixed(1)}`,
    status: r.severity,
    time: "—",
    statusColor:
      r.severity === "critical"
        ? "text-red-400"
        : r.severity === "high"
        ? "text-orange-400"
        : "text-amber-400",
  }));

  return [...sRows, ...rRows].slice(-12).reverse();
}

export default function TransactionsTable() {
  const settlements = useAgentStore((s) => s.settlements);
  const riskAlerts = useAgentStore((s) => s.riskAlerts);

  const rows = buildRows(settlements, riskAlerts);

  return (
    <div className="card span-full animate-fade-in">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-zinc-200">
          Transaction Ledger
        </h3>
        <span className="text-[10px] text-zinc-600 font-mono">
          {rows.length} rows
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="tx-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Type</th>
              <th>Description</th>
              <th>Amount / Score</th>
              <th>Status</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td colSpan={6} className="text-center text-zinc-600 py-6">
                  No transactions yet
                </td>
              </tr>
            )}
            {rows.map((row) => (
              <tr key={row.id}>
                <td className="font-mono text-zinc-500">{row.id}</td>
                <td>
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded ${
                      row.type === "settlement"
                        ? "badge-web3"
                        : "badge-fintech"
                    }`}
                  >
                    {row.type}
                  </span>
                </td>
                <td>{row.description}</td>
                <td className="font-mono">{row.amount}</td>
                <td className={row.statusColor}>{row.status}</td>
                <td className="text-zinc-500 font-mono">{row.time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

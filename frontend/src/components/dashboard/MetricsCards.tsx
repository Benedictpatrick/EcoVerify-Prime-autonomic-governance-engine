import { useAgentStore } from "../../stores/agentStore";
import type { Settlement, RiskAlert } from "../../lib/types";

interface MetricCardProps {
  label: string;
  value: string;
  delta?: string;
  deltaUp?: boolean;
  icon?: React.ReactNode;
}

function MetricCard({ label, value, delta, deltaUp, icon }: MetricCardProps) {
  return (
    <div className="card-sm flex flex-col gap-2 animate-fade-in">
      <div className="flex items-center justify-between">
        <span className="metric-label">{label}</span>
        {icon && <span className="text-zinc-500">{icon}</span>}
      </div>
      <div className="metric-value">{value}</div>
      {delta && (
        <span className={deltaUp ? "metric-delta-up" : "metric-delta-down"}>
          {deltaUp ? "↑" : "↓"} {delta}
        </span>
      )}
    </div>
  );
}

function formatUSD(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(2)}`;
}

export default function MetricsCards() {
  const settlements = useAgentStore((s) => s.settlements);
  const riskAlerts = useAgentStore((s) => s.riskAlerts);
  const governorAction = useAgentStore((s) => s.governorAction);

  // Aggregated metrics
  const totalSettled = settlements.reduce(
    (sum: number, s: Settlement) => sum + (s.amount_usdc ?? 0),
    0
  );

  const activeRisks = riskAlerts.filter(
    (r: RiskAlert) => r.severity === "critical" || r.severity === "high"
  ).length;

  const avgRisk =
    riskAlerts.length > 0
      ? riskAlerts.reduce((sum: number, r: RiskAlert) => sum + r.score, 0) /
        riskAlerts.length
      : 0;

  const roi = governorAction?.estimated_roi ?? 0;

  return (
    <div className="grid grid-cols-4 gap-4 span-full">
      <MetricCard
        label="Total Volume"
        value={formatUSD(totalSettled)}
        delta={settlements.length > 0 ? `${settlements.length} txns` : undefined}
        deltaUp={settlements.length > 0}
        icon={
          <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 16 16">
            <path d="M2 12l3-4 3 2 3-5 3 1" />
          </svg>
        }
      />
      <MetricCard
        label="Risk Score"
        value={avgRisk > 0 ? avgRisk.toFixed(1) : "—"}
        delta={activeRisks > 0 ? `${activeRisks} active` : "clear"}
        deltaUp={activeRisks === 0}
      />
      <MetricCard
        label="CO₂ Saved"
        value={roi > 0 ? `${((roi * 12 * 0.000417 * 3) / 0.18).toFixed(1)}t` : "—"}
        delta="tons/yr"
        deltaUp
      />
      <MetricCard
        label="Est. ROI"
        value={roi > 0 ? formatUSD(roi) : "—"}
        delta={
          governorAction?.npv_3yr
            ? formatUSD(governorAction.npv_3yr)
            : undefined
        }
        deltaUp={!!governorAction?.npv_3yr && governorAction.npv_3yr > 0}
      />
    </div>
  );
}

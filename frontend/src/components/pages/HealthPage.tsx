/**
 * HealthPage — FHIR audits, facility compliance, and energy efficiency monitoring.
 */

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAgentStore } from "../../stores/agentStore";
import type { FHIRAudit } from "../../lib/types";

// Demo FHIR audit data
const demoAudits: FHIRAudit[] = [
  {
    facility_id: "HQ-01",
    facility_type: "Corporate HQ",
    energy_efficiency_score: 87.3,
    benchmark_percentile: 92,
    recommendations: ["Upgrade HVAC to VRF system", "Install smart lighting sensors", "Add solar thermal panels"],
    compliance_status: "compliant",
    timestamp: new Date(Date.now() - 300_000).toISOString(),
  },
  {
    facility_id: "DC-02",
    facility_type: "Data Center",
    energy_efficiency_score: 72.1,
    benchmark_percentile: 65,
    recommendations: ["Implement hot/cold aisle containment", "Upgrade to liquid cooling", "Optimize server utilization"],
    compliance_status: "review_needed",
    timestamp: new Date(Date.now() - 120_000).toISOString(),
  },
  {
    facility_id: "MFG-03",
    facility_type: "Manufacturing",
    energy_efficiency_score: 64.8,
    benchmark_percentile: 48,
    recommendations: ["Install variable frequency drives", "Replace aging boilers", "Add waste heat recovery", "Improve insulation"],
    compliance_status: "non_compliant",
    timestamp: new Date(Date.now() - 60_000).toISOString(),
  },
  {
    facility_id: "WH-04",
    facility_type: "Warehouse",
    energy_efficiency_score: 91.2,
    benchmark_percentile: 96,
    recommendations: ["Maintain current systems", "Consider EV charging stations"],
    compliance_status: "compliant",
    timestamp: new Date(Date.now() - 30_000).toISOString(),
  },
];

function EfficiencyGauge({ score, label, size = 80 }: { score: number; label: string; size?: number }) {
  const pct = Math.min(score, 100);
  const color = score >= 80 ? "#22c55e" : score >= 60 ? "#f59e0b" : "#ef4444";
  const radius = (size - 12) / 2;
  const circumference = radius * 2 * Math.PI;

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: size, height: size }}>
        <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-full -rotate-90">
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="6" />
          <circle
            cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={color} strokeWidth="6"
            strokeDasharray={`${(pct / 100) * circumference} ${circumference}`}
            strokeLinecap="round"
            className="transition-all duration-700"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-sm font-bold" style={{ color }}>{score.toFixed(0)}</span>
        </div>
      </div>
      <span className="text-[9px] text-zinc-500 uppercase tracking-wider">{label}</span>
    </div>
  );
}

function statusColor(status: string): { bg: string; text: string; label: string } {
  switch (status) {
    case "compliant": return { bg: "bg-green-500/10", text: "text-green-400", label: "Compliant" };
    case "review_needed": return { bg: "bg-amber-500/10", text: "text-amber-400", label: "Review Needed" };
    case "non_compliant": return { bg: "bg-red-500/10", text: "text-red-400", label: "Non-Compliant" };
    default: return { bg: "bg-zinc-800", text: "text-zinc-400", label: status };
  }
}

function FacilityCard({ audit, index }: { audit: FHIRAudit; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const sc = statusColor(audit.compliance_status);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08 }}
      className="card-sm cursor-pointer transition-all hover:border-zinc-600"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <EfficiencyGauge score={audit.energy_efficiency_score} label="" size={56} />
          <div>
            <h3 className="text-sm font-bold text-zinc-200">{audit.facility_id}</h3>
            <p className="text-[10px] text-zinc-500">{audit.facility_type}</p>
          </div>
        </div>
        <span className={`text-[9px] px-2 py-0.5 rounded ${sc.bg} ${sc.text}`}>
          {sc.label}
        </span>
      </div>

      {/* Benchmark bar */}
      <div className="mb-2">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[9px] text-zinc-500">Benchmark Percentile</span>
          <span className="text-[9px] text-zinc-400 font-mono">{audit.benchmark_percentile}th</span>
        </div>
        <div className="w-full h-1.5 rounded-full bg-zinc-800 overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${audit.benchmark_percentile}%` }}
            transition={{ duration: 0.6, delay: index * 0.1 }}
            className="h-full rounded-full"
            style={{
              background: audit.benchmark_percentile >= 80 ? "#22c55e" :
                audit.benchmark_percentile >= 50 ? "#f59e0b" : "#ef4444",
            }}
          />
        </div>
      </div>

      {/* Expandable recommendations */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-3 pt-3 border-t border-zinc-800/50">
              <span className="text-[9px] text-zinc-500 uppercase tracking-wider">Recommendations</span>
              <div className="mt-1.5 space-y-1">
                {audit.recommendations.map((rec, i) => (
                  <div key={i} className="flex items-start gap-2 px-2 py-1 rounded bg-zinc-900/40">
                    <span className="text-[8px] text-blue-400 mt-0.5">→</span>
                    <span className="text-[10px] text-zinc-400">{rec}</span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="mt-2 text-[8px] text-zinc-600 text-center">
        {expanded ? "▲ Click to collapse" : "▼ Click for recommendations"}
      </div>
    </motion.div>
  );
}

export default function HealthPage() {
  const storeFhir = useAgentStore((s) => s.fhirAudits);

  // Use store data if available, else demo data
  const audits = storeFhir.length > 0 ? storeFhir : demoAudits;

  const avgScore = audits.reduce((sum, a) => sum + a.energy_efficiency_score, 0) / Math.max(audits.length, 1);
  const compliantCount = audits.filter((a) => a.compliance_status === "compliant").length;
  const reviewCount = audits.filter((a) => a.compliance_status === "review_needed").length;
  const nonCompliant = audits.filter((a) => a.compliance_status === "non_compliant").length;

  return (
    <div className="dashboard-main">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-zinc-100">Health & Compliance</h1>
            <p className="text-xs text-zinc-500 mt-0.5">
              FHIR-integrated facility audits, energy efficiency, and ESG compliance monitoring
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="badge-health text-[9px] px-2 py-0.5">FHIR R4</span>
          </div>
        </div>

        {/* Summary metrics */}
        <div className="grid grid-cols-4 gap-4">
          <div className="card-sm text-center">
            <EfficiencyGauge score={avgScore} label="Avg Efficiency" />
          </div>
          <div className="card-sm flex flex-col items-center justify-center gap-1">
            <span className="text-2xl font-bold text-green-400">{compliantCount}</span>
            <span className="metric-label">Compliant</span>
            <span className="text-[9px] text-zinc-600">of {audits.length} facilities</span>
          </div>
          <div className="card-sm flex flex-col items-center justify-center gap-1">
            <span className="text-2xl font-bold text-amber-400">{reviewCount}</span>
            <span className="metric-label">Review Needed</span>
          </div>
          <div className="card-sm flex flex-col items-center justify-center gap-1">
            <span className="text-2xl font-bold text-red-400">{nonCompliant}</span>
            <span className="metric-label">Non-Compliant</span>
          </div>
        </div>

        {/* Compliance overview bar */}
        <div className="card">
          <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">
            Compliance Distribution
          </h3>
          <div className="flex h-4 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(compliantCount / Math.max(audits.length, 1)) * 100}%` }}
              transition={{ duration: 0.6 }}
              className="bg-green-500/60 h-full"
              title={`${compliantCount} compliant`}
            />
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(reviewCount / Math.max(audits.length, 1)) * 100}%` }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="bg-amber-500/60 h-full"
              title={`${reviewCount} review needed`}
            />
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(nonCompliant / Math.max(audits.length, 1)) * 100}%` }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="bg-red-500/60 h-full"
              title={`${nonCompliant} non-compliant`}
            />
          </div>
          <div className="flex items-center gap-4 mt-2">
            <span className="flex items-center gap-1 text-[9px] text-zinc-500"><span className="w-2 h-2 rounded-sm bg-green-500/60" /> Compliant</span>
            <span className="flex items-center gap-1 text-[9px] text-zinc-500"><span className="w-2 h-2 rounded-sm bg-amber-500/60" /> Review</span>
            <span className="flex items-center gap-1 text-[9px] text-zinc-500"><span className="w-2 h-2 rounded-sm bg-red-500/60" /> Non-Compliant</span>
          </div>
        </div>

        {/* Facility cards */}
        <div className="grid grid-cols-2 gap-4">
          {audits.map((audit, i) => (
            <FacilityCard key={audit.facility_id} audit={audit} index={i} />
          ))}
        </div>
      </div>
    </div>
  );
}

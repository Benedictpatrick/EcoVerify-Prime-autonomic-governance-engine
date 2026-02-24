/**
 * Zustand store — single source of truth for the EcoVerify dashboard.
 */

import { create } from "zustand";
import type {
  DashboardConfig,
  DecisionTrace,
  EdutechHint,
  FHIRAudit,
  GovernorAction,
  NeuralFeedEntry,
  RiskAlert,
  SceneData,
  Settlement,
} from "../lib/types";

export type PageId = "dashboard" | "agents" | "finance" | "health" | "settings";

interface AgentStore {
  // ── State ────────────────────────────────────────────
  activePage: PageId;
  threadId: string | null;
  isRunning: boolean;
  currentPhase: string;
  neuralFeed: NeuralFeedEntry[];
  sceneData: SceneData | null;
  proofGraph: string | null;
  governorAction: GovernorAction | null;
  decisionTraces: DecisionTrace[];
  showProofGraph: boolean;

  // ── Domain expansion state ───────────────────────────
  settlements: Settlement[];
  riskAlerts: RiskAlert[];
  fhirAudits: FHIRAudit[];
  edutechHints: EdutechHint[];
  dashboardConfig: DashboardConfig | null;
  weeklyActivity: number[];
  selectedRackId: string | null;

  // ── Actions ──────────────────────────────────────────
  setActivePage: (page: PageId) => void;
  setThreadId: (id: string) => void;
  setIsRunning: (running: boolean) => void;
  setCurrentPhase: (phase: string) => void;
  addFeedEntry: (entry: NeuralFeedEntry) => void;
  updateScene: (data: SceneData) => void;
  setProofGraph: (mermaid: string) => void;
  setGovernorAction: (action: GovernorAction | null) => void;
  addDecisionTrace: (trace: DecisionTrace) => void;
  toggleProofGraph: () => void;
  addSettlement: (s: Settlement) => void;
  addRiskAlert: (r: RiskAlert) => void;
  addFhirAudit: (a: FHIRAudit) => void;
  addEdutechHint: (h: EdutechHint) => void;
  setDashboardConfig: (cfg: DashboardConfig) => void;
  setWeeklyActivity: (data: number[]) => void;
  setSelectedRackId: (id: string | null) => void;
  reset: () => void;
}

const NOW = new Date().toISOString();
const seedFeed: NeuralFeedEntry[] = [
  { id: "seed-1", agent: "SYSTEM", message: "EcoVerify-Prime initialised — 4 agents online, NHI keys verified", severity: "low", timestamp: NOW, feedType: "neural_feed" },
  { id: "seed-2", agent: "VANGUARD", message: "BMS telemetry stream connected — monitoring HQ-01 (energy + water)", severity: "low", timestamp: NOW, feedType: "neural_feed" },
  { id: "seed-3", agent: "JURIST", message: "EU AI Act regulatory corpus loaded — 847 articles indexed", severity: "low", timestamp: NOW, feedType: "neural_feed" },
  { id: "seed-4", agent: "ARCHITECT", message: "Monte Carlo simulation engine ready — 10,000 iteration capacity", severity: "low", timestamp: NOW, feedType: "neural_feed" },
  { id: "seed-5", agent: "GOVERNOR", message: "HITL approval pipeline active — awaiting anomaly trigger", severity: "medium", timestamp: NOW, feedType: "neural_feed" },
];

const initialState = {
  activePage: "dashboard" as PageId,
  threadId: null as string | null,
  isRunning: false,
  currentPhase: "idle",
  neuralFeed: seedFeed,
  sceneData: null as SceneData | null,
  proofGraph: null as string | null,
  governorAction: null as GovernorAction | null,
  decisionTraces: [] as DecisionTrace[],
  showProofGraph: false,
  settlements: [] as Settlement[],
  riskAlerts: [] as RiskAlert[],
  fhirAudits: [] as FHIRAudit[],
  edutechHints: [] as EdutechHint[],
  dashboardConfig: null as DashboardConfig | null,
  weeklyActivity: [12, 24, 18, 31, 27, 14, 8] as number[],
  selectedRackId: null as string | null,
};

export const useAgentStore = create<AgentStore>((set) => ({
  ...initialState,

  setActivePage: (page) => set({ activePage: page }),
  setThreadId: (id) => set({ threadId: id }),
  setIsRunning: (running) => set({ isRunning: running }),
  setCurrentPhase: (phase) => set({ currentPhase: phase }),

  addFeedEntry: (entry) =>
    set((s) => ({
      neuralFeed: [...s.neuralFeed, entry].slice(-100),
      weeklyActivity: (() => {
        const day = new Date().getDay();
        const arr = [...s.weeklyActivity];
        arr[day === 0 ? 6 : day - 1] += 1;
        return arr;
      })(),
    })),

  updateScene: (data) => set({ sceneData: data }),
  setProofGraph: (mermaid) => set({ proofGraph: mermaid }),
  setGovernorAction: (action) => set({ governorAction: action }),

  addDecisionTrace: (trace) =>
    set((s) => ({ decisionTraces: [...s.decisionTraces, trace] })),

  toggleProofGraph: () => set((s) => ({ showProofGraph: !s.showProofGraph })),

  addSettlement: (s) => set((state) => ({ settlements: [...state.settlements, s] })),
  addRiskAlert: (r) => set((state) => ({ riskAlerts: [...state.riskAlerts, r] })),
  addFhirAudit: (a) => set((state) => ({ fhirAudits: [...state.fhirAudits, a] })),
  addEdutechHint: (h) => set((state) => ({ edutechHints: [...state.edutechHints, h] })),
  setDashboardConfig: (cfg) => set({ dashboardConfig: cfg }),
  setWeeklyActivity: (data) => set({ weeklyActivity: data }),
  setSelectedRackId: (id) => set({ selectedRackId: id }),

  reset: () => set(initialState),
}));

/**
 * Dashboard — Finance Report–style CSS Grid layout with page routing.
 *
 * Layout:
 *   ┌─────┬────────────────────────────────┬──────────┐
 *   │ Nav │  Top Bar (StatusBar)           │          │
 *   │     ├────────────────────────────────┤ Governor │
 *   │     │  Page Content (routed)         │ Panel    │
 *   │     │                                │ (side)   │
 *   └─────┴────────────────────────────────┴──────────┘
 */

import { lazy, Suspense } from "react";
import NavSidebar from "./NavSidebar";
import StatusBar from "./StatusBar";
import MetricsCards from "./MetricsCards";
import VolumeChart from "./VolumeChart";
import RecentEvents from "./RecentEvents";
import NeuralFeed from "./NeuralFeed";
import ActivityPanel from "./ActivityPanel";
import TransactionsTable from "./TransactionsTable";
import ProofGraph from "./ProofGraph";
import GovernorPanel from "./GovernorPanel";
import AgentsPage from "../pages/AgentsPage";
import FinancePage from "../pages/FinancePage";
import HealthPage from "../pages/HealthPage";
import SettingsPage from "../pages/SettingsPage";
import { useAgentStore } from "../../stores/agentStore";

const DigitalTwin = lazy(() => import("../three/DigitalTwin"));

function TwinFallback() {
  return (
    <div className="w-full h-full flex items-center justify-center" style={{ minHeight: 360 }}>
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-blue-500/20 border-t-blue-500 rounded-full animate-spin mx-auto mb-3" />
        <p className="text-[10px] text-zinc-500 uppercase tracking-widest">
          Loading 3D Engine
        </p>
      </div>
    </div>
  );
}

function TwinPlaceholder() {
  return (
    <div className="w-full h-full flex items-center justify-center" style={{ minHeight: 360 }}>
      <div className="text-center opacity-60">
        <svg width="48" height="48" fill="none" stroke="currentColor" strokeWidth="1" viewBox="0 0 24 24" className="mx-auto mb-3 text-zinc-600">
          <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z" />
          <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
          <line x1="12" y1="22.08" x2="12" y2="12" />
        </svg>
        <p className="text-[11px] text-zinc-500 font-medium">Digital Twin — Standby</p>
        <p className="text-[10px] text-zinc-600 mt-1">Spawns on anomaly detection</p>
      </div>
    </div>
  );
}

function DashboardHome() {
  const sceneData = useAgentStore((s) => s.sceneData);

  return (
    <div className="dashboard-main">
      <div className="main-grid">
        {/* Row 1: Metrics */}
        <MetricsCards />

        {/* Row 2: Chart + Events */}
        <VolumeChart />
        <RecentEvents />

        {/* Row 3: Twin (conditional) + Feed */}
        <div className="span-2 card overflow-hidden" style={{ minHeight: 360 }}>
          {sceneData ? (
            <Suspense fallback={<TwinFallback />}>
              <DigitalTwin />
            </Suspense>
          ) : (
            <TwinPlaceholder />
          )}
        </div>
        <NeuralFeed />

        {/* Row 4: Activity + Transactions */}
        <ActivityPanel />
        <TransactionsTable />

        {/* Row 5: Proof Graph */}
        <ProofGraph />
      </div>
    </div>
  );
}

function PageContent() {
  const activePage = useAgentStore((s) => s.activePage);

  switch (activePage) {
    case "agents": return <AgentsPage />;
    case "finance": return <FinancePage />;
    case "health": return <HealthPage />;
    case "settings": return <SettingsPage />;
    default: return <DashboardHome />;
  }
}

export default function Dashboard() {
  return (
    <div className="dashboard-grid noise-overlay">
      {/* Left nav */}
      <NavSidebar />

      {/* Top bar */}
      <StatusBar />

      {/* Routed page content */}
      <PageContent />

      {/* Right sidebar */}
      <GovernorPanel />
    </div>
  );
}

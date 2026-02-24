import { type ReactNode } from "react";
import { useAgentStore, type PageId } from "../../stores/agentStore";

type NavItem = {
  id: PageId;
  label: string;
  icon: ReactNode;
};

/* Simple SVG icons (20×20) */
const icons = {
  dashboard: (
    <svg width="20" height="20" fill="none" viewBox="0 0 20 20" stroke="currentColor" strokeWidth="1.5">
      <rect x="2" y="2" width="7" height="7" rx="1.5" />
      <rect x="11" y="2" width="7" height="7" rx="1.5" />
      <rect x="2" y="11" width="7" height="7" rx="1.5" />
      <rect x="11" y="11" width="7" height="7" rx="1.5" />
    </svg>
  ),
  agents: (
    <svg width="20" height="20" fill="none" viewBox="0 0 20 20" stroke="currentColor" strokeWidth="1.5">
      <circle cx="10" cy="6" r="3" />
      <path d="M3 17c0-3.3 2.7-6 7-6s7 2.7 7 6" />
    </svg>
  ),
  finance: (
    <svg width="20" height="20" fill="none" viewBox="0 0 20 20" stroke="currentColor" strokeWidth="1.5">
      <path d="M2 16l4-5 4 3 4-6 4 2" />
      <path d="M2 18h16" />
    </svg>
  ),
  health: (
    <svg width="20" height="20" fill="none" viewBox="0 0 20 20" stroke="currentColor" strokeWidth="1.5">
      <path d="M10 3l-1 4H5l3 3-1 4 3-2 3 2-1-4 3-3h-4z" />
    </svg>
  ),
  settings: (
    <svg width="20" height="20" fill="none" viewBox="0 0 20 20" stroke="currentColor" strokeWidth="1.5">
      <circle cx="10" cy="10" r="3" />
      <path d="M10 1v3M10 16v3M1 10h3M16 10h3M3.5 3.5l2 2M14.5 14.5l2 2M3.5 16.5l2-2M14.5 5.5l2-2" />
    </svg>
  ),
};

const navItems: NavItem[] = [
  { id: "dashboard", label: "Dashboard", icon: icons.dashboard },
  { id: "agents", label: "Agents", icon: icons.agents },
  { id: "finance", label: "Finance", icon: icons.finance },
  { id: "health", label: "Health", icon: icons.health },
  { id: "settings", label: "Settings", icon: icons.settings },
];

export default function NavSidebar() {
  const active = useAgentStore((s) => s.activePage);
  const setActivePage = useAgentStore((s) => s.setActivePage);

  return (
    <nav className="nav-sidebar dashboard-nav">
      {/* Logo */}
      <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600">
        <span className="text-sm font-bold text-white">EV</span>
      </div>

      {/* Nav items */}
      <div className="flex flex-col gap-1 mt-2">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActivePage(item.id)}
            className={`nav-icon ${active === item.id ? "active" : ""}`}
            title={item.label}
          >
            {item.icon}
          </button>
        ))}
      </div>

      {/* Spacer + bottom indicator */}
      <div className="mt-auto mb-4">
        <div className="status-dot status-dot-live mx-auto" />
      </div>
    </nav>
  );
}

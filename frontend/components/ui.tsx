import Link from "next/link";
import {
  BadgeCheck,
  Blocks,
  FileSearch,
  Gauge,
  MapPinned,
  Play,
  Workflow,
} from "lucide-react";
import type { BackendHealth } from "@/lib/api";

export type Tone = "good" | "warn" | "bad" | "neutral" | "live";

export function StatusPill({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: Tone;
}) {
  return <span className={`status-pill ${tone}`}>{children}</span>;
}

export function stateTone(state?: string | null): Tone {
  if (!state) return "neutral";
  const normalized = state.toLowerCase();
  if (["complete", "completed", "approved", "parsed", "healthy", "settled"].includes(normalized)) {
    return "good";
  }
  if (
    [
      "review",
      "needs review",
      "in review",
      "running",
      "processing",
      "verification_in_progress",
      "settlement_pending",
      "funded",
      "degraded",
    ].includes(normalized)
  ) {
    return "warn";
  }
  if (["blocked", "high", "failed", "unhealthy", "cancelled", "disputed"].includes(normalized)) {
    return "bad";
  }
  if (["queued", "pending", "initiated", "assigned"].includes(normalized)) {
    return "live";
  }
  return "neutral";
}

export function IconButton({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <button className="icon-button" aria-label={label} title={label}>
      {children}
    </button>
  );
}

const navItems = [
  { label: "Deals", href: "/deals", icon: Blocks },
  { label: "Diligence", href: "/properties/search", icon: FileSearch },
  { label: "Escrow", href: "/transactions", icon: Workflow },
  { label: "Health", href: "/health", icon: Gauge },
  { label: "Trust", href: "/trust", icon: BadgeCheck },
  { label: "Map", href: "/", icon: MapPinned },
];

export function AppHeader({ health }: { health: BackendHealth | null }) {
  const apiOnline = health?.status === "healthy";

  return (
    <header className="topbar">
      <Link className="brand" href="/">
        <span className="brand-mark">C</span>
        <span>
          <strong>Counter</strong>
          <small>Escrow Console</small>
        </span>
      </Link>

      <nav className="nav" aria-label="Primary">
        {navItems.map((item) => (
          <Link href={item.href} key={`${item.label}-${item.href}`}>
            <item.icon size={15} />
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="top-actions">
        <StatusPill tone={apiOnline ? "good" : "bad"}>
          {apiOnline ? "API live" : "API offline"}
        </StatusPill>
        <Link className="primary-action" href="/properties/search">
          <Play size={15} />
          Run workflow
        </Link>
      </div>
    </header>
  );
}

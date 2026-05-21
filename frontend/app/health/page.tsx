import { AppHeader, stateTone, StatusPill } from "@/components/ui";
import { getBackendHealth, getDependencyHealth, getReadinessHealth } from "@/lib/api";

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="json-block">{JSON.stringify(value, null, 2)}</pre>;
}

export default async function HealthPage() {
  const [health, readiness, dependencies] = await Promise.all([
    getBackendHealth(),
    getReadinessHealth(),
    getDependencyHealth(),
  ]);

  return (
    <main className="shell">
      <AppHeader health={health} />
      <section className="workspace-header compact">
        <div>
          <div className="eyebrow">Infrastructure readiness</div>
          <h1>System health</h1>
          <p>
            Inspect backend readiness, dependency status, and operational signals before
            running escrow or diligence workflows.
          </p>
        </div>
      </section>

      <section className="detail-grid">
        <section className="panel">
          <div className="panel-heading">
            <h2>Liveness</h2>
            <StatusPill tone={stateTone(health?.status)}>{health?.status ?? "offline"}</StatusPill>
          </div>
          <JsonBlock value={health ?? { status: "unreachable" }} />
        </section>

        <section className="panel">
          <div className="panel-heading">
            <h2>Readiness</h2>
            <StatusPill tone={readiness.ok ? "good" : "bad"}>{readiness.ok ? "loaded" : "error"}</StatusPill>
          </div>
          <JsonBlock value={readiness.ok ? readiness.data : readiness} />
        </section>
      </section>

      <section className="page-panel">
        <div className="panel-heading">
          <h2>Dependencies</h2>
          <StatusPill tone={dependencies.ok ? "good" : "bad"}>
            {dependencies.ok ? "loaded" : "error"}
          </StatusPill>
        </div>
        <JsonBlock value={dependencies.ok ? dependencies.data : dependencies} />
      </section>
    </main>
  );
}

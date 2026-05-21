import Link from "next/link";
import { ArrowRight, BadgeCheck, FileCheck2, History, ShieldCheck } from "lucide-react";
import { AppHeader, stateTone, StatusPill } from "@/components/ui";
import {
  getBackendHealth,
  getReadinessHealth,
  listEvents,
  listTransactions,
} from "@/lib/api";

export default async function TrustPage() {
  const [health, readiness, transactionsResult] = await Promise.all([
    getBackendHealth(),
    getReadinessHealth(),
    listTransactions(),
  ]);

  const transactions = transactionsResult.ok ? transactionsResult.data.transactions : [];
  const eventResults = await Promise.all(
    transactions.map((transaction) => listEvents(transaction.id)),
  );
  const auditCounts = new Map(
    transactions.map((transaction, index) => [
      transaction.id,
      eventResults[index]?.ok ? eventResults[index].data.total : 0,
    ]),
  );
  const auditableDeals = transactions.filter(
    (transaction) => (auditCounts.get(transaction.id) ?? 0) > 0,
  ).length;
  const totalEvents = [...auditCounts.values()].reduce((sum, count) => sum + count, 0);
  const reviewStates = transactions.filter((transaction) =>
    ["verification_in_progress", "disputed", "settlement_pending"].includes(transaction.state),
  ).length;

  return (
    <main className="shell">
      <AppHeader health={health} />
      <section className="workspace-header compact">
        <div>
          <div className="eyebrow">Trust layer</div>
          <h1>Trust</h1>
          <p>
            Inspect whether AI workflow outputs are backed by evidence, auditable events, and
            human-review states. Health remains the raw infrastructure readiness view.
          </p>
        </div>
        <div className="header-ops">
          <Link className="secondary-action" href="/health">
            System health
          </Link>
        </div>
      </section>

      <section className="deal-summary-grid" aria-label="Trust metrics">
        <article className="metric">
          <span>Auditable workflows</span>
          <strong>
            {auditableDeals}/{transactions.length}
          </strong>
          <small>transactions with recorded backend events</small>
        </article>
        <article className="metric">
          <span>Audit events</span>
          <strong>{totalEvents}</strong>
          <small>settlement, funding, dispute, and verification records</small>
        </article>
        <article className="metric">
          <span>Human review</span>
          <strong>{reviewStates}</strong>
          <small>items requiring expert inspection</small>
        </article>
        <article className="metric">
          <span>Readiness</span>
          <strong className="metric-word">{readiness.ok ? "Loaded" : "Error"}</strong>
          <small>backend readiness endpoint status</small>
        </article>
      </section>

      <section className="detail-grid">
        <section className="panel">
          <div className="panel-heading">
            <h2>Trust controls</h2>
            <StatusPill tone="good">Inspectable</StatusPill>
          </div>
          <div className="trust-control-list">
            <span>
              <BadgeCheck size={18} />
              <strong>Source-backed recommendations</strong>
              <small>Risk and diligence outputs keep the cited issue visible to reviewers.</small>
            </span>
            <span>
              <History size={18} />
              <strong>Auditable state changes</strong>
              <small>Escrow state transitions are paired with backend event records.</small>
            </span>
            <span>
              <ShieldCheck size={18} />
              <strong>Human-in-the-loop release</strong>
              <small>Disputed and pending workflows remain visible before settlement action.</small>
            </span>
          </div>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <h2>Evidence posture</h2>
            <StatusPill tone={transactionsResult.ok ? "good" : "bad"}>
              {transactionsResult.ok ? "synced" : "error"}
            </StatusPill>
          </div>
          <div className="trust-control-list">
            <span>
              <FileCheck2 size={18} />
              <strong>{transactions.length} backend examples</strong>
              <small>Current test set covers active, funded, disputed, pending, settled, and cancelled states.</small>
            </span>
            <span>
              <History size={18} />
              <strong>{totalEvents} recorded events</strong>
              <small>Event counts are loaded from the escrow audit endpoints, not hardcoded UI data.</small>
            </span>
            <span>
              <ShieldCheck size={18} />
              <strong>{health?.status ?? "offline"} service signal</strong>
              <small>Infrastructure detail remains available from the health page.</small>
            </span>
          </div>
        </section>
      </section>

      <section className="page-panel">
        <div className="panel-heading">
          <h2>Workflow audit coverage</h2>
          {transactionsResult.ok ? (
            <StatusPill tone="live">{transactions.length} workflows</StatusPill>
          ) : (
            <StatusPill tone="bad">Backend error</StatusPill>
          )}
        </div>

        {!transactionsResult.ok ? (
          <div className="empty-state compact-state">{transactionsResult.error}</div>
        ) : (
          <div className="data-table">
            <div className="data-row header">
              <span>Workflow</span>
              <span>State</span>
              <span>Events</span>
              <span>Review posture</span>
              <span />
            </div>
            {transactions.map((transaction) => {
              const events = auditCounts.get(transaction.id) ?? 0;
              const needsReview = ["verification_in_progress", "disputed", "settlement_pending"].includes(
                transaction.state,
              );

              return (
                <Link className="data-row" href={`/transactions/${transaction.id}`} key={transaction.id}>
                  <span>
                    <strong>{String(transaction.metadata?.address ?? transaction.property_id)}</strong>
                    <small>{transaction.id}</small>
                  </span>
                  <StatusPill tone={stateTone(transaction.state)}>
                    {transaction.state.replaceAll("_", " ")}
                  </StatusPill>
                  <span>{events} audit events</span>
                  <span>{needsReview ? "Expert review required" : "No active review hold"}</span>
                  <span className="row-action">
                    Inspect
                    <ArrowRight size={14} />
                  </span>
                </Link>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}

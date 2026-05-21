import Link from "next/link";
import {
  ArrowRight,
  CircleAlert,
  FileSearch,
  Landmark,
  ListChecks,
  Search,
  WalletCards,
} from "lucide-react";
import { AppHeader, stateTone, StatusPill, type Tone } from "@/components/ui";
import { getBackendHealth, listTransactions, type Transaction } from "@/lib/api";

type DealPhase = {
  label: string;
  tone: Tone;
  summary: string;
  nextStep: string;
  missing: string[];
};

function currency(value: string | number) {
  return `$${Number(value).toLocaleString()}`;
}

function dealPhase(transaction: Transaction): DealPhase {
  switch (transaction.state) {
    case "verification_in_progress":
      return {
        label: "Diligence review",
        tone: "warn",
        summary: "Agent review is active and expert approvals are still shaping the escrow recommendation.",
        nextStep: "Resolve diligence exceptions",
        missing: ["Inspection approval", "Appraisal confirmation"],
      };
    case "funded":
      return {
        label: "Escrow handoff",
        tone: "live",
        summary: "Earnest money is in place and the deal is ready for verification assignment.",
        nextStep: "Assign verification package",
        missing: ["Title search", "Inspection order"],
      };
    case "disputed":
      return {
        label: "Risk intervention",
        tone: "bad",
        summary: "The acquisition has a material objection that needs expert review before next action.",
        nextStep: "Review dispute evidence",
        missing: ["Buyer decision", "Repair or cancellation memo"],
      };
    case "settlement_pending":
      return {
        label: "Closing review",
        tone: "warn",
        summary: "Most diligence is complete; lender or settlement conditions remain before release.",
        nextStep: "Clear closing conditions",
        missing: ["Lender condition", "Final settlement approval"],
      };
    case "settled":
      return {
        label: "Closed",
        tone: "good",
        summary: "Deal completed with escrow settlement and an auditable transaction history.",
        nextStep: "Archive deal package",
        missing: ["Post-close memo"],
      };
    case "cancelled":
      return {
        label: "Cancelled",
        tone: "bad",
        summary: "The acquisition was stopped and escrow activity should be treated as historical.",
        nextStep: "Review cancellation reason",
        missing: ["Lessons learned", "Refund confirmation"],
      };
    default:
      return {
        label: "Intake",
        tone: stateTone(transaction.state),
        summary: "Deal is captured and needs AI diligence before escrow operations take over.",
        nextStep: "Start diligence workflow",
        missing: ["Document package", "Risk analysis"],
      };
  }
}

export default async function DealsPage() {
  const [health, transactionsResult] = await Promise.all([
    getBackendHealth(),
    listTransactions(),
  ]);

  const transactions = transactionsResult.ok ? transactionsResult.data.transactions : [];
  const pipelineValue = transactions.reduce(
    (sum, transaction) => sum + Number(transaction.total_purchase_price),
    0,
  );
  const reviewCount = transactions.filter((transaction) =>
    ["verification_in_progress", "disputed", "settlement_pending"].includes(transaction.state),
  ).length;
  const closedCount = transactions.filter((transaction) =>
    ["settled", "cancelled"].includes(transaction.state),
  ).length;

  return (
    <main className="shell">
      <AppHeader health={health} />
      <section className="workspace-header compact">
        <div>
          <div className="eyebrow">Acquisition pipeline</div>
          <h1>Deals</h1>
          <p>
            Prioritize opportunities, inspect diligence blockers, and decide which assets are ready
            to hand off into escrow operations.
          </p>
        </div>
        <div className="header-ops">
          <Link className="primary-action" href="/properties/search">
            <Search size={15} />
            Source deals
          </Link>
        </div>
      </section>

      <section className="deal-summary-grid" aria-label="Deal pipeline metrics">
        <article className="metric">
          <span>Pipeline value</span>
          <strong>{currency(pipelineValue)}</strong>
          <small>synced from backend transactions</small>
        </article>
        <article className="metric">
          <span>Needs review</span>
          <strong>{reviewCount}</strong>
          <small>diligence or closing items open</small>
        </article>
        <article className="metric">
          <span>Escrow-ready</span>
          <strong>
            {transactions.filter((transaction) => transaction.state === "funded").length}
          </strong>
          <small>funded and ready for task assignment</small>
        </article>
        <article className="metric">
          <span>Closed / stopped</span>
          <strong>{closedCount}</strong>
          <small>settled or cancelled examples</small>
        </article>
      </section>

      <section className="page-panel">
        <div className="panel-heading">
          <h2>Deal worklist</h2>
          {transactionsResult.ok ? (
            <StatusPill tone="good">{transactionsResult.data.total} synced</StatusPill>
          ) : (
            <StatusPill tone="bad">Backend error</StatusPill>
          )}
        </div>

        {!transactionsResult.ok ? (
          <div className="empty-state">
            <strong>Could not load deals</strong>
            <small>{transactionsResult.error}</small>
          </div>
        ) : transactions.length === 0 ? (
          <div className="empty-state">
            <strong>No deals are available</strong>
            <small>Use property search to create acquisition candidates for review.</small>
          </div>
        ) : (
          <div className="deal-card-grid">
            {transactions.map((transaction) => {
              const phase = dealPhase(transaction);
              const address = String(transaction.metadata?.address ?? transaction.property_id);

              return (
                <article className="deal-card" key={transaction.id}>
                  <div className="deal-card-top">
                    <span>
                      <strong>{address}</strong>
                      <small>{String(transaction.metadata?.market ?? "Market pending")}</small>
                    </span>
                    <StatusPill tone={phase.tone}>{phase.label}</StatusPill>
                  </div>

                  <p>{phase.summary}</p>

                  <div className="signal-list">
                    <span className="signal-row">
                      <FileSearch size={16} />
                      <strong>{phase.nextStep}</strong>
                    </span>
                    <span className="signal-row">
                      <WalletCards size={16} />
                      <strong>{currency(transaction.earnest_money)} earnest money</strong>
                    </span>
                    <span className="signal-row">
                      <Landmark size={16} />
                      <strong>{currency(transaction.total_purchase_price)} purchase price</strong>
                    </span>
                  </div>

                  <div className="deal-missing">
                    <span>
                      <ListChecks size={15} />
                      Open items
                    </span>
                    {phase.missing.map((item) => (
                      <small key={item}>{item}</small>
                    ))}
                  </div>

                  <div className="deal-card-actions">
                    <Link className="text-action" href="/properties/search">
                      Run diligence
                      <ArrowRight size={14} />
                    </Link>
                    <Link className="secondary-action" href={`/transactions/${transaction.id}`}>
                      Open escrow
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      <section className="handoff-strip">
        <CircleAlert size={18} />
        <span>
          Deals use the same backend transaction graph, but this screen frames it as acquisition
          intake and diligence. Escrow keeps the operational payment, verification, and audit view.
        </span>
      </section>
    </main>
  );
}

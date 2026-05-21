import Link from "next/link";
import { ArrowRight, Plus } from "lucide-react";
import { AppHeader, stateTone, StatusPill } from "@/components/ui";
import { getBackendHealth, listTransactions } from "@/lib/api";

export default async function TransactionsPage() {
  const [health, transactionsResult] = await Promise.all([
    getBackendHealth(),
    listTransactions(),
  ]);

  const transactions = transactionsResult.ok ? transactionsResult.data.transactions : [];

  return (
    <main className="shell">
      <AppHeader health={health} />
      <section className="workspace-header compact">
        <div>
          <div className="eyebrow">Escrow operations</div>
          <h1>Transactions</h1>
          <p>Track escrow state, verification readiness, payments, settlement, and auditability.</p>
        </div>
        <div className="header-ops">
          <Link className="primary-action" href="/properties/search">
            <Plus size={15} />
            Source property
          </Link>
        </div>
      </section>

      <section className="page-panel">
        <div className="panel-heading">
          <h2>Live backend transactions</h2>
          {transactionsResult.ok ? (
            <StatusPill tone="good">{transactionsResult.data.total} total</StatusPill>
          ) : (
            <StatusPill tone="bad">Backend error</StatusPill>
          )}
        </div>

        {!transactionsResult.ok ? (
          <div className="empty-state">
            <strong>Could not load transactions</strong>
            <small>{transactionsResult.error}</small>
          </div>
        ) : transactions.length === 0 ? (
          <div className="empty-state">
            <strong>No escrow transactions yet</strong>
            <small>Use property search and offer drafting to create a transaction-ready deal.</small>
          </div>
        ) : (
          <div className="data-table">
            <div className="data-row header">
              <span>Property</span>
              <span>State</span>
              <span>Purchase price</span>
              <span>Closing target</span>
              <span />
            </div>
            {transactions.map((transaction) => (
              <Link className="data-row" href={`/transactions/${transaction.id}`} key={transaction.id}>
                <span>
                  <strong>{transaction.metadata?.address?.toString() || transaction.property_id}</strong>
                  <small>{transaction.id}</small>
                </span>
                <StatusPill tone={stateTone(transaction.state)}>
                  {transaction.state.replaceAll("_", " ")}
                </StatusPill>
                <span>${Number(transaction.total_purchase_price).toLocaleString()}</span>
                <span>{new Date(transaction.target_closing_date).toLocaleDateString()}</span>
                <span className="row-action">
                  Open
                  <ArrowRight size={14} />
                </span>
              </Link>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

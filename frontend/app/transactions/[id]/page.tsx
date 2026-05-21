import Link from "next/link";
import { ArrowLeft, ExternalLink, RefreshCw } from "lucide-react";
import { AppHeader, stateTone, StatusPill } from "@/components/ui";
import {
  getBackendHealth,
  getTransaction,
  listEvents,
  listPayments,
  listVerificationTasks,
} from "@/lib/api";

export default async function TransactionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [health, transactionResult, verificationResult, paymentResult, eventResult] =
    await Promise.all([
      getBackendHealth(),
      getTransaction(id),
      listVerificationTasks(id),
      listPayments(id),
      listEvents(id),
    ]);

  return (
    <main className="shell">
      <AppHeader health={health} />
      <section className="workspace-header compact">
        <div>
          <Link className="text-action back-link" href="/transactions">
            <ArrowLeft size={14} />
            Transactions
          </Link>
          <div className="eyebrow">Escrow transaction</div>
          <h1>
            {transactionResult.ok
              ? String(transactionResult.data.metadata?.address ?? transactionResult.data.property_id)
              : "Transaction"}
          </h1>
          <p>
            Inspect verification tasks, payment release state, settlement readiness, and audit
            events for this escrow workflow.
          </p>
        </div>
      </section>

      {!transactionResult.ok ? (
        <section className="page-panel">
          <div className="empty-state">
            <strong>Transaction unavailable</strong>
            <small>{transactionResult.error}</small>
          </div>
        </section>
      ) : (
        <>
          <section className="metrics-grid">
            <article className="metric">
              <span>State</span>
              <strong className="metric-word">{transactionResult.data.state.replaceAll("_", " ")}</strong>
              <small>current lifecycle position</small>
            </article>
            <article className="metric">
              <span>Purchase price</span>
              <strong>${Number(transactionResult.data.total_purchase_price).toLocaleString()}</strong>
              <small>total contract value</small>
            </article>
            <article className="metric">
              <span>Earnest money</span>
              <strong>${Number(transactionResult.data.earnest_money).toLocaleString()}</strong>
              <small>wallet funding basis</small>
            </article>
            <article className="metric">
              <span>Target close</span>
              <strong className="metric-word">
                {new Date(transactionResult.data.target_closing_date).toLocaleDateString()}
              </strong>
              <small>scheduled settlement date</small>
            </article>
          </section>

          <section className="detail-grid">
            <section className="panel">
              <div className="panel-heading">
                <h2>Verification tasks</h2>
                {verificationResult.ok ? (
                  <StatusPill tone="live">{verificationResult.data.total} tasks</StatusPill>
                ) : (
                  <StatusPill tone="bad">Error</StatusPill>
                )}
              </div>
              {!verificationResult.ok ? (
                <div className="empty-state compact-state">{verificationResult.error}</div>
              ) : verificationResult.data.tasks.length === 0 ? (
                <div className="empty-state compact-state">No verification tasks are attached yet.</div>
              ) : (
                <div className="data-table embedded">
                  {verificationResult.data.tasks.map((task) => (
                    <div className="data-row" key={task.id}>
                      <span>
                        <strong>{task.verification_type.replaceAll("_", " ")}</strong>
                        <small>{task.assigned_agent_id}</small>
                      </span>
                      <StatusPill tone={stateTone(task.status)}>{task.status}</StatusPill>
                      <span>${Number(task.payment_amount).toLocaleString()}</span>
                      <span>{new Date(task.deadline).toLocaleDateString()}</span>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="panel">
              <div className="panel-heading">
                <h2>Payments</h2>
                {paymentResult.ok ? (
                  <StatusPill tone="live">{paymentResult.data.total} payments</StatusPill>
                ) : (
                  <StatusPill tone="bad">Error</StatusPill>
                )}
              </div>
              {!paymentResult.ok ? (
                <div className="empty-state compact-state">{paymentResult.error}</div>
              ) : paymentResult.data.payments.length === 0 ? (
                <div className="empty-state compact-state">No payment records are available.</div>
              ) : (
                <div className="data-table embedded">
                  {paymentResult.data.payments.map((payment) => (
                    <div className="data-row" key={payment.id}>
                      <span>
                        <strong>{payment.payment_type.replaceAll("_", " ")}</strong>
                        <small>{payment.recipient_id}</small>
                      </span>
                      <StatusPill tone={stateTone(payment.status)}>{payment.status}</StatusPill>
                      <span>${Number(payment.amount).toLocaleString()}</span>
                      <span className="row-action">
                        <RefreshCw size={14} />
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </section>

          <section className="page-panel">
            <div className="panel-heading">
              <h2>Audit events</h2>
              {eventResult.ok ? (
                <StatusPill tone="good">{eventResult.data.total} events</StatusPill>
              ) : (
                <StatusPill tone="bad">Error</StatusPill>
              )}
            </div>
            {!eventResult.ok ? (
              <div className="empty-state compact-state">{eventResult.error}</div>
            ) : eventResult.data.events.length === 0 ? (
              <div className="empty-state compact-state">No audit events have been recorded yet.</div>
            ) : (
              <div className="data-table">
                {eventResult.data.events.map((event) => (
                  <div className="data-row" key={event.id}>
                    <span>
                      <strong>{event.event_type.replaceAll("_", " ")}</strong>
                      <small>{new Date(event.timestamp).toLocaleString()}</small>
                    </span>
                    <span>{event.blockchain_tx_hash ?? "No hash"}</span>
                    <span>{event.block_number ?? "Pending block"}</span>
                    <span className="row-action">
                      Verify
                      <ExternalLink size={14} />
                    </span>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </main>
  );
}

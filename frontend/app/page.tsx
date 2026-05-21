import {
  ArrowRight,
  Check,
  ChevronDown,
  CircleAlert,
  Download,
  ExternalLink,
  FileUp,
  Gauge,
  History,
  MessageSquareText,
  Search,
  Shield,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { getBackendHealth, listTransactions } from "@/lib/api";
import { AppHeader, IconButton, stateTone, StatusPill } from "@/components/ui";
import {
  agents,
  deals,
  documents,
  escrowMilestones,
  metrics,
  traceEvents,
  workflowSteps,
} from "@/lib/data";

export default async function Home() {
  const [health, transactionsResult] = await Promise.all([
    getBackendHealth(),
    listTransactions(),
  ]);
  const transactions = transactionsResult.ok ? transactionsResult.data.transactions : [];
  const activeDeals =
    transactions.length > 0
      ? transactions.slice(0, 5).map((transaction) => ({
          name: transaction.metadata?.address?.toString() || transaction.property_id,
          market: `Buyer ${transaction.buyer_agent_id}`,
          phase: transaction.state.replaceAll("_", " "),
          risk: transaction.state,
          value: `$${Number(transaction.total_purchase_price).toLocaleString()}`,
          href: "/deals",
        }))
      : deals.map((deal) => ({ ...deal, href: "/properties/search" }));

  return (
    <main className="shell">
      <AppHeader health={health} />

      <section className="workspace-header">
        <div>
          <div className="eyebrow">
            <Sparkles size={15} />
            AI diligence and transaction execution
          </div>
          <h1>567 Guilford Avenue</h1>
          <p>
            Multi-agent diligence workspace for source-backed risk review,
            verification approvals, and escrow settlement readiness.
          </p>
        </div>

        <div className="header-ops">
          <Link className="secondary-action" href="/properties/search">
            <FileUp size={15} />
            Add files
          </Link>
          <Link className="secondary-action" href="/properties/search">
            <MessageSquareText size={15} />
            Ask agent
          </Link>
          <Link className="secondary-action" href="/transactions">
            <Download size={15} />
            Export
          </Link>
        </div>
      </section>

      <section className="metrics-grid" aria-label="Operating metrics">
        {[
          {
            label: "Active workflows",
            value: String(transactions.length || metrics[0].value),
            detail: transactions.length ? "live escrow transactions" : metrics[0].detail,
          },
          ...metrics.slice(1),
        ].map((metric) => (
          <article className="metric" key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
            <small>{metric.detail}</small>
          </article>
        ))}
      </section>

      <section className="console-grid">
        <aside className="rail">
          <div className="rail-header">
            <h2>Active deals</h2>
            <IconButton label="Search deals">
              <Search size={16} />
            </IconButton>
          </div>

          <div className="deal-list">
            {activeDeals.map((deal, index) => (
              <Link className={`deal-row ${index === 0 ? "active" : ""}`} href={deal.href} key={deal.name}>
                <span>
                  <strong>{deal.name}</strong>
                  <small>{deal.market}</small>
                </span>
                <span className="deal-meta">
                  <StatusPill tone={stateTone(deal.risk)}>{deal.risk}</StatusPill>
                  <small>{deal.phase}</small>
                </span>
              </Link>
            ))}
          </div>

          <div className="operator-note">
            <Gauge size={18} />
            <span>
              <strong>Backend</strong>
              <small>
                {transactionsResult.ok
                  ? `${transactionsResult.data.total} transactions available`
                  : transactionsResult.error}
              </small>
            </span>
          </div>
        </aside>

        <section className="main-stack">
          <div className="section-heading">
            <span>Agent workflow</span>
            <Link className="text-action" href="/deals">
              View deals
              <ArrowRight size={14} />
            </Link>
          </div>

          <div className="workflow-board">
            {workflowSteps.map((step, index) => (
              <article className="workflow-step" key={step.title}>
                <div className="step-index">{String(index + 1).padStart(2, "0")}</div>
                <div>
                  <div className="step-title">
                    <h3>{step.title}</h3>
                    <StatusPill tone={stateTone(step.state)}>{step.state}</StatusPill>
                  </div>
                  <p>{step.detail}</p>
                  <small>{step.owner}</small>
                </div>
              </article>
            ))}
          </div>

          <div className="split-grid">
            <section className="panel">
              <div className="panel-heading">
                <h2>Document review</h2>
                <Link className="text-action" href="/deals">
                  Sort
                  <ChevronDown size={14} />
                </Link>
              </div>

              <div className="document-table">
                {documents.map((doc) => (
                  <div className="document-row" key={doc.name}>
                    <span>
                      <strong>{doc.name}</strong>
                      <small>{doc.type}</small>
                    </span>
                    <span>{doc.issue}</span>
                    <span>{doc.citations} cites</span>
                    <StatusPill tone={stateTone(doc.status)}>{doc.status}</StatusPill>
                  </div>
                ))}
              </div>
            </section>

            <section className="panel">
              <div className="panel-heading">
                <h2>Escrow state</h2>
                <StatusPill tone="warn">2 approvals pending</StatusPill>
              </div>

              <div className="milestones">
                {escrowMilestones.map((milestone) => (
                  <div className="milestone" key={milestone.label}>
                    <div className="milestone-icon">
                      <milestone.icon size={17} />
                    </div>
                    <span>
                      <strong>{milestone.label}</strong>
                      <small>{milestone.value}</small>
                    </span>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <div className="split-grid">
            <section className="panel">
              <div className="panel-heading">
                <h2>Agent bench</h2>
                <StatusPill tone="live">LangGraph run</StatusPill>
              </div>

              <div className="agent-grid">
                {agents.map((agent) => (
                  <article className="agent-card" key={agent.name}>
                    <agent.icon size={18} />
                    <span>
                      <strong>{agent.name}</strong>
                      <small>{agent.task}</small>
                    </span>
                    <StatusPill tone={stateTone(agent.state)}>{agent.state}</StatusPill>
                    <small>{agent.tool}</small>
                  </article>
                ))}
              </div>
            </section>

            <section className="panel">
              <div className="panel-heading">
                <h2>Geospatial constraints</h2>
                <Link className="text-action" href="/trust">
                  Sources
                  <ExternalLink size={14} />
                </Link>
              </div>

              <div className="map-surface" aria-label="Parcel feasibility map">
                <div className="parcel primary">
                  <span>Subject parcel</span>
                </div>
                <div className="parcel flood">Flood overlay</div>
                <div className="parcel utility">Utility easement</div>
                <div className="parcel comp">Comp 01</div>
                <div className="parcel comp two">Comp 02</div>
              </div>
            </section>
          </div>
        </section>

        <aside className="right-stack">
          <section className="panel review-panel">
            <div className="panel-heading">
              <h2>Expert review</h2>
              <Shield size={18} />
            </div>
            <div className="review-callout">
              <CircleAlert size={18} />
              <span>
                <strong>Electrical exception</strong>
                <small>Agent needs buyer approval before release recommendation.</small>
              </span>
            </div>
            <div className="review-actions">
              <Link className="approve-action" href="/transactions">
                <Check size={15} />
                Approve
              </Link>
              <Link className="secondary-action" href="/transactions">Request changes</Link>
            </div>
          </section>

          <section className="panel">
            <div className="panel-heading">
              <h2>Trace</h2>
              <History size={18} />
            </div>
            <div className="trace-list">
              {traceEvents.map((event) => (
                <article className="trace-event" key={`${event.time}-${event.title}`}>
                  <time>{event.time}</time>
                  <span>
                    <strong>{event.title}</strong>
                    <small>{event.body}</small>
                  </span>
                </article>
              ))}
            </div>
          </section>

          <section className="panel">
            <div className="panel-heading">
              <h2>Quality gates</h2>
              <StatusPill tone="good">Inspectable</StatusPill>
            </div>
            <div className="quality-list">
              <span>
                <strong>18 / 19</strong>
                <small>extractions pass schema</small>
              </span>
              <span>
                <strong>0</strong>
                <small>unsupported claims</small>
              </span>
              <span>
                <strong>842ms</strong>
                <small>median tool latency</small>
              </span>
            </div>
          </section>
        </aside>
      </section>
    </main>
  );
}

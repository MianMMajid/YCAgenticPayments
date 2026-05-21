import { AppHeader } from "@/components/ui";
import { getBackendHealth } from "@/lib/api";
import { PropertySearchClient } from "./property-search-client";

export default async function PropertySearchPage() {
  const health = await getBackendHealth();

  return (
    <main className="shell">
      <AppHeader health={health} />
      <section className="workspace-header compact">
        <div>
          <div className="eyebrow">Diligence intake</div>
          <h1>Property search</h1>
          <p>
            Search properties, inspect source-backed risk flags, and promote promising deals
            into the escrow workflow.
          </p>
        </div>
      </section>
      <PropertySearchClient />
    </main>
  );
}

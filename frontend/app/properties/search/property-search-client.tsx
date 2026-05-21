"use client";

import { useState } from "react";
import { AlertTriangle, Search } from "lucide-react";
import {
  API_BASE_URL,
  type PropertyResult,
  type RiskResponse,
  type SearchPayload,
  type SearchResponse,
} from "@/lib/api";
import { stateTone, StatusPill } from "@/components/ui";

type RequestState = "idle" | "loading" | "success" | "error";

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      detail = payload.detail ?? detail;
    } catch {
      detail = response.statusText || detail;
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

export function PropertySearchClient() {
  const [status, setStatus] = useState<RequestState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<PropertyResult[]>([]);
  const [riskByProperty, setRiskByProperty] = useState<Record<string, RiskResponse>>({});

  async function onSubmit(formData: FormData) {
    setStatus("loading");
    setError(null);

    const payload: SearchPayload = {
      location: String(formData.get("location") || "Baltimore, MD"),
      user_id: String(formData.get("user_id") || "demo_user"),
      max_price: Number(formData.get("max_price") || 0) || undefined,
      min_beds: Number(formData.get("min_beds") || 0) || undefined,
      min_baths: Number(formData.get("min_baths") || 0) || undefined,
    };

    try {
      const response = await postJson<SearchResponse>("/tools/search", payload);
      setResults(response.properties);
      setStatus("success");
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Search failed";
      setError(`Search failed: ${message}`);
      setResults([]);
      setStatus("error");
    }
  }

  async function analyzeRisk(property: PropertyResult) {
    setError(null);

    try {
      const risk = await postJson<RiskResponse>("/tools/analyze-risk", {
        property_id: property.property_id,
        address: property.address,
        list_price: property.price,
        user_id: "demo_user",
      });
      setRiskByProperty((current) => ({
        ...current,
        [property.property_id]: risk,
      }));
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Risk analysis failed";
      setError(`Risk analysis failed: ${message}`);
    }
  }

  return (
    <section className="search-layout">
      <form action={onSubmit} className="panel form-panel">
        <div className="panel-heading">
          <h2>Search criteria</h2>
          <StatusPill tone={status === "success" ? "good" : status === "error" ? "bad" : "neutral"}>
            {status}
          </StatusPill>
        </div>
        <div className="form-grid">
          <label>
            Location
            <input name="location" defaultValue="Baltimore, MD" />
          </label>
          <label>
            Max price
            <input name="max_price" defaultValue="400000" inputMode="numeric" />
          </label>
          <label>
            Min beds
            <input name="min_beds" defaultValue="3" inputMode="numeric" />
          </label>
          <label>
            Min baths
            <input name="min_baths" defaultValue="2" inputMode="numeric" />
          </label>
          <input name="user_id" type="hidden" value="demo_user" readOnly />
        </div>
        <button className="primary-action form-submit" disabled={status === "loading"}>
          <Search size={15} />
          {status === "loading" ? "Searching..." : "Search properties"}
        </button>
      </form>

      <div className="main-stack">
        {error ? (
          <div className="panel error-panel">
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        ) : null}

        <section className="page-panel">
          <div className="panel-heading">
            <h2>Results</h2>
            <StatusPill tone="live">{results.length} properties</StatusPill>
          </div>
          {results.length === 0 ? (
            <div className="empty-state">
              <strong>No properties loaded</strong>
              <small>Run a search to call the FastAPI property search tool.</small>
            </div>
          ) : (
            <div className="property-grid">
              {results.map((property) => {
                const risk = riskByProperty[property.property_id];
                return (
                  <article className="property-card" key={property.property_id}>
                    <div className="property-card-head">
                      <span>
                        <strong>{property.address}</strong>
                        <small>{property.beds} beds / {property.baths} baths / {property.sqft ?? "N/A"} sqft</small>
                      </span>
                      <strong>${property.price.toLocaleString()}</strong>
                    </div>
                    <p>{property.summary || "No AI summary returned."}</p>
                    <div className="property-actions">
                      <button className="secondary-action" onClick={() => analyzeRisk(property)} type="button">
                        Analyze risk
                      </button>
                      {property.listing_url ? (
                        <a className="text-action" href={property.listing_url} rel="noreferrer" target="_blank">
                          Listing
                        </a>
                      ) : null}
                    </div>
                    {risk ? (
                      <div className="risk-box">
                        <StatusPill tone={stateTone(risk.overall_risk)}>{risk.overall_risk} risk</StatusPill>
                        {risk.flags.length === 0 ? (
                          <small>No risk flags returned.</small>
                        ) : (
                          risk.flags.map((flag) => (
                            <span key={`${property.property_id}-${flag.category}-${flag.message}`}>
                              <strong>{flag.category}</strong>
                              <small>{flag.message}</small>
                            </span>
                          ))
                        )}
                      </div>
                    ) : null}
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </section>
  );
}

// src/components/SummaryMetrics.tsx
import React, { useEffect, useState } from "react";

const API_BASE = "http://localhost:8000";

type SummaryRow = {
  metric: string;
  value: string | number;
};

const SummaryMetrics: React.FC = () => {
  const [data, setData] = useState<SummaryRow[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<string | null>(null);

  const fetchSummary = async () => {
    try {
      setLoading(true);
      setError(null);

      const res = await fetch(`${API_BASE}/api/metrics/summary`);
      if (!res.ok) {
        if (res.status === 503) {
          setData(null);
          setError("Summary metrics not ready yet.");
          return;
        }
        throw new Error(`HTTP ${res.status}`);
      }

      const json = (await res.json()) as SummaryRow[];
      setData(json);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err: any) {
      setError(err.message ?? "Failed to load summary metrics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;

    const load = () => {
      if (!cancelled) {
        fetchSummary();
      }
    };

    // initial load
    load();

    // auto-refresh every 10s (summary changes slower than live counts)
    const id = setInterval(load, 10_000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  // helper to grab metric by name
  const getMetric = (name: string): string | number | null => {
    if (!data) return null;
    const row = data.find((r) => r.metric === name);
    return row ? row.value : null;
  };

  const minEventTime = getMetric("min_event_time");
  const maxEventTime = getMetric("max_event_time");
  const distinctUsers = getMetric("distinct_users");

  return (
    <section className="card">
      <h2 className="card-title">Summary Metrics</h2>

      <p className="card-text card-text-muted">
        High-level snapshot of the data processed by the system.
        {lastRefreshed && ` · Last updated: ${lastRefreshed}`}
      </p>

      {loading && !data && !error && (
        <p className="card-text">Loading summary metrics…</p>
      )}

      {error && (
        <p className="card-text card-text-error">{error}</p>
      )}

      {data && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(0, 1.1fr) minmax(0, 1fr)",
            gap: "0.75rem",
            marginTop: "0.5rem",
          }}
        >
          {/* Big distinct users metric */}
          <div
            style={{
              borderRadius: "0.75rem",
              border: "1px solid #1f2937",
              padding: "0.75rem 1rem",
              background:
                "radial-gradient(circle at top left, rgba(34,197,94,0.18), transparent 55%)",
            }}
          >
            <div
              style={{
                fontSize: "0.85rem",
                color: "#9ca3af",
                marginBottom: "0.25rem",
              }}
            >
              Distinct users
            </div>
            <div
              style={{
                fontSize: "1.6rem",
                fontWeight: 600,
              }}
            >
              {distinctUsers !== null ? distinctUsers : "—"}
            </div>
            <div
              style={{
                fontSize: "0.8rem",
                color: "#9ca3af",
                marginTop: "0.25rem",
              }}
            >
              Total unique viewers tracked in the current dataset.
            </div>
          </div>

          {/* Time range block */}
          <div
            style={{
              borderRadius: "0.75rem",
              border: "1px solid #1f2937",
              padding: "0.75rem 1rem",
              background:
                "radial-gradient(circle at top right, rgba(56,189,248,0.18), transparent 55%)",
            }}
          >
            <div
              style={{
                fontSize: "0.85rem",
                color: "#9ca3af",
                marginBottom: "0.4rem",
              }}
            >
              Event time range (UTC)
            </div>

            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "0.25rem",
                fontSize: "0.85rem",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                }}
              >
                <span style={{ color: "#9ca3af" }}>Earliest event</span>
                <span>
                  {minEventTime ? String(minEventTime) : "—"}
                </span>
              </div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                }}
              >
                <span style={{ color: "#9ca3af" }}>Latest event</span>
                <span>
                  {maxEventTime ? String(maxEventTime) : "—"}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {!loading && !error && !data && (
        <p className="card-text card-text-muted">
          No summary metrics available.
        </p>
      )}
    </section>
  );
};

export default SummaryMetrics;
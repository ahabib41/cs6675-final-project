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

    load();
    const id = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const getValue = (metric: string) =>
    data?.find((m) => m.metric === metric)?.value ?? null;

  const minEventTime = getValue("min_event_time");
  const maxEventTime = getValue("max_event_time");
  const distinctUsers = getValue("distinct_users");
  const totalEvents = getValue("total_events");
  const eventsLast5 = getValue("events_last_5_min");

  return (
    <section className="card">
      <h2 className="card-title">Summary Metrics</h2>

      {lastRefreshed && (
        <p className="card-text card-text-muted">
          Auto-refreshing every 5s · Last updated: {lastRefreshed}
        </p>
      )}

      {loading && !data && !error && (
        <p className="card-text">Loading summary metrics…</p>
      )}

      {error && (
        <p className="card-text card-text-error">{error}</p>
      )}

      {data && data.length > 0 && (
        <>
          <table className="metrics-table">
            <thead>
              <tr>
                <th>Time Window</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>First event seen</td>
                <td>{minEventTime ?? "—"}</td>
              </tr>
              <tr>
                <td>Latest event seen</td>
                <td>{maxEventTime ?? "—"}</td>
              </tr>
            </tbody>
          </table>

          <table className="metrics-table" style={{ marginTop: "0.75rem" }}>
            <thead>
              <tr>
                <th>Traffic</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Distinct users</td>
                <td>
                  {distinctUsers !== null ? distinctUsers.toString() : "—"}
                </td>
              </tr>
              <tr>
                <td>Total events</td>
                <td>
                  {totalEvents !== null ? totalEvents.toString() : "—"}
                </td>
              </tr>
              <tr>
                <td>Events in last 5 min</td>
                <td>
                  {eventsLast5 !== null ? eventsLast5.toString() : "—"}
                </td>
              </tr>
            </tbody>
          </table>
        </>
      )}

      {!loading && !error && (!data || data.length === 0) && (
        <p className="card-text card-text-muted">
          No summary metrics available yet.
        </p>
      )}
    </section>
  );
};

export default SummaryMetrics;
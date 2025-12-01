import React, { useEffect, useState } from "react";

const API_BASE = "http://localhost:8000";

type MetricInfo = {
  ready: boolean;
  latest_file: string | null;
  last_updated: string | null;
};

type HealthResponse = {
  status: string;
  event_type_metrics: MetricInfo;
  summary_metrics: MetricInfo;
};

const HealthStatus: React.FC = () => {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const fetchHealth = async () => {
      try {
        setLoading(true);
        setError(null);

        const res = await fetch(`${API_BASE}/api/health`);
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const json = (await res.json()) as HealthResponse;
        if (!cancelled) {
          setData(json);
        }
      } catch (err: any) {
        if (!cancelled) {
          setError(err.message ?? "Failed to load backend health");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchHealth();
    const id = setInterval(fetchHealth, 5000);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const formatFileLabel = (
    file: string | null,
    kind: "event" | "summary"
  ): string => {
    if (!file) return "—";

    if (file.startsWith("part-") && file.includes(".parquet")) {
      return kind === "event"
        ? "event_type_counts (latest batch)"
        : "summary_metrics (latest batch)";
    }

    return file;
  };

  if (loading && !data && !error) {
    return (
      <section className="card">
        <h2 className="card-title">Backend Health</h2>
        <p className="card-text">Checking backend health…</p>
      </section>
    );
  }

  if (error || !data) {
    return (
      <section className="card">
        <h2 className="card-title">Backend Health</h2>
        <p className="card-text card-text-error">
          Failed to load backend health: {error ?? "unknown error"}
        </p>
      </section>
    );
  }

  const { status, event_type_metrics, summary_metrics } = data;

  const statusLabel =
    status === "ok" ? "All systems operational" : status.toUpperCase();

  return (
    <section className="card">
      <h2 className="card-title">Backend Health</h2>

      
      <div className="health-api-row">
        <span className="health-label">API Status</span>
        <span
          className={`health-status-pill ${
            status === "ok" ? "health-status-ok" : "health-status-bad"
          }`}
        >
          {statusLabel}
        </span>
      </div>

      <div className="health-grid">
        <div className="health-block">
          <div className="health-block-header">
            <span className="health-block-title">Event-Type Metrics</span>
            <span
              className={
                event_type_metrics.ready
                  ? "health-chip health-chip-ok"
                  : "health-chip health-chip-bad"
              }
            >
              {event_type_metrics.ready ? "Ready" : "Not ready"}
            </span>
          </div>
          <div className="health-block-body">
            <div className="health-row">
              <span className="health-key">Latest file</span>
              <span className="health-value mono">
                {formatFileLabel(event_type_metrics.latest_file, "event")}
              </span>
            </div>
            <div className="health-row">
              <span className="health-key">Updated</span>
              <span className="health-value">
                {event_type_metrics.last_updated ?? "—"}
              </span>
            </div>
          </div>
        </div>

        {/* Summary block */}
        <div className="health-block">
          <div className="health-block-header">
            <span className="health-block-title">Summary Metrics</span>
            <span
              className={
                summary_metrics.ready
                  ? "health-chip health-chip-ok"
                  : "health-chip health-chip-bad"
              }
            >
              {summary_metrics.ready ? "Ready" : "Not ready"}
            </span>
          </div>
          <div className="health-block-body">
            <div className="health-row">
              <span className="health-key">Latest file</span>
              <span className="health-value mono">
                {formatFileLabel(summary_metrics.latest_file, "summary")}
              </span>
            </div>
            <div className="health-row">
              <span className="health-key">Updated</span>
              <span className="health-value">
                {summary_metrics.last_updated ?? "—"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HealthStatus;
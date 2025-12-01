import React, { useEffect, useState } from "react";

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

const API_BASE = "http://localhost:8000";

const HealthStatus: React.FC = () => {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showEventRealFile, setShowEventRealFile] = useState(false);
  const [showSummaryRealFile, setShowSummaryRealFile] = useState(false);

  const fetchHealth = async () => {
    try {
      setError(null);
      const res = await fetch(`${API_BASE}/api/health`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = (await res.json()) as HealthResponse;
      setData(json);
    } catch (err: any) {
      setError(err.message ?? "Failed to fetch health");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // first load
    fetchHealth();

    // auto-refresh every 5 seconds
    const id = setInterval(fetchHealth, 5000);
    return () => clearInterval(id);
  }, []);

  // Helper: friendly label vs real filename
  const getDisplayFileLabel = (
    file: string | null,
    kind: "event" | "summary",
    showReal: boolean
  ): string => {
    if (!file) return "—";
    if (showReal) return file;

    if (file.startsWith("part-") && file.includes(".parquet")) {
      return kind === "event"
        ? "event_type_counts.pq (latest batch)"
        : "summary_metrics.pq (latest batch)";
    }

    return file;
  };

  return (
    <section className="card">
      <h2 className="card-title">Backend Health</h2>

      {loading && !data && <p>Loading health...</p>}
      {error && <p className="error">Error: {error}</p>}

      {data && (
        <div className="health-grid">
          {/* API status */}
          <div>
            <div className="label">API Status</div>
            <div className="pill pill-ok">{data.status}</div>
          </div>

          {/* Event-type metrics */}
          <div>
            <div className="label">Event-Type Metrics</div>
            <div>
              {data.event_type_metrics.ready ? "Ready ✅" : "Not ready ❌"}
            </div>

            {data.event_type_metrics.latest_file && (
              <div className="subtext">
                <div>
                  Latest file:{" "}
                  {getDisplayFileLabel(
                    data.event_type_metrics.latest_file,
                    "event",
                    showEventRealFile
                  )}
                </div>
                <button
                  type="button"
                  className="btn-secondary"
                  style={{ marginTop: "0.25rem" }}
                  onClick={() => setShowEventRealFile((prev) => !prev)}
                >
                  {showEventRealFile ? "Hide actual name" : "Show actual name"}
                </button>
                <div>Updated: {data.event_type_metrics.last_updated}</div>
              </div>
            )}
          </div>

          {/* Summary metrics */}
          <div>
            <div className="label">Summary Metrics</div>
            <div>
              {data.summary_metrics.ready ? "Ready" : "Not ready"}
            </div>

            {data.summary_metrics.latest_file && (
              <div className="subtext">
                <div>
                  Latest file:{" "}
                  {getDisplayFileLabel(
                    data.summary_metrics.latest_file,
                    "summary",
                    showSummaryRealFile
                  )}
                </div>
                <button
                  type="button"
                  className="btn-secondary"
                  style={{ marginTop: "0.25rem" }}
                  onClick={() => setShowSummaryRealFile((prev) => !prev)}
                >
                  {showSummaryRealFile ? "Hide actual name" : "Show actual name"}
                </button>
                <div>Updated: {data.summary_metrics.last_updated}</div>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
};

export default HealthStatus;
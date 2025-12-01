// src/components/EventTypeMetrics.tsx
import React, { useEffect, useState } from "react";

const API_BASE = "http://localhost:8000";

type EventTypeRow = {
  event_type: string;
  count: number;
};

const WINDOW_OPTIONS = [0, 1, 5, 15];

const EventTypeMetrics: React.FC = () => {
  const [data, setData] = useState<EventTypeRow[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 0 = all time, >0 = last N minutes
  const [windowMinutes, setWindowMinutes] = useState<number>(0);
  const [lastRefreshed, setLastRefreshed] = useState<string | null>(null);

  const fetchMetrics = async (minutes: number) => {
    try {
      setLoading(true);
      setError(null);

      const url =
        minutes > 0
          ? `${API_BASE}/api/metrics/event-type?minutes=${minutes}`
          : `${API_BASE}/api/metrics/event-type`;

      const res = await fetch(url);
      if (!res.ok) {
        if (res.status === 503) {
          setData(null);
          setError("Event-type metrics not ready yet.");
          return;
        }
        throw new Error(`HTTP ${res.status}`);
      }

      const json = (await res.json()) as EventTypeRow[];
      setData(json);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err: any) {
      setError(err.message ?? "Failed to load event-type metrics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;

    const load = () => {
      if (!cancelled) {
        fetchMetrics(windowMinutes);
      }
    };

    // initial load
    load();

    // auto-refresh every 5 seconds
    const id = setInterval(load, 5000);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [windowMinutes]);

  const handleWindowChange = (
    e: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const minutes = Number(e.target.value);
    setWindowMinutes(minutes);
  };

  const windowLabel =
    windowMinutes === 0
      ? "All available events"
      : `Last ${windowMinutes} minute${windowMinutes === 1 ? "" : "s"}`;

  // 🔹 Small summary strip over the table
  let totalEvents = 0;
  let topEventType: string | null = null;
  let clickCount: number | null = null;
  let maxCount = 0;

  if (data && data.length > 0) {
    totalEvents = data.reduce((sum, row) => sum + row.count, 0);
    topEventType = data[0].event_type;
    const clickRow = data.find((r) => r.event_type === "click");
    clickCount = clickRow ? clickRow.count : null;
    maxCount = data.reduce(
      (max, row) => (row.count > max ? row.count : max),
      0
    );
  }

  const formatShare = (count: number) => {
    if (!totalEvents) return "—";
    const pct = (count / totalEvents) * 100;
    return `${pct.toFixed(1)}%`;
  };

  const barWidth = (count: number) => {
    if (!maxCount) return "0%";
    // width relative to max, but with a minimum so tiny numbers are still visible
    const pct = (count / maxCount) * 100;
    const clamped = Math.max(6, pct); // minimum 6%
    return `${Math.min(clamped, 100)}%`;
  };

  return (
    <section className="card">
      <div className="card-header-row">
        <h2 className="card-title">Event-Type Metrics (Live)</h2>

        <div className="card-controls">
          <span className="toggle-label">
            <span>Window:</span>
            <select
              value={windowMinutes}
              onChange={handleWindowChange}
              style={{
                background: "#020617",
                borderRadius: "999px",
                border: "1px solid #334155",
                color: "#e5e7eb",
                fontSize: "0.85rem",
                padding: "0.25rem 0.6rem",
              }}
            >
              {WINDOW_OPTIONS.map((m) => (
                <option key={m} value={m}>
                  {m === 0 ? "All time" : `Last ${m} min`}
                </option>
              ))}
            </select>
          </span>
        </div>
      </div>

      {/* Info line under header */}
      <p className="card-text card-text-muted">
        Showing: {windowLabel}
        {lastRefreshed && ` · Last updated: ${lastRefreshed}`}
      </p>

      {/* 🔹 Summary strip */}
      {data && data.length > 0 && (
        <div
          style={{
            marginBottom: "0.6rem",
            display: "flex",
            flexWrap: "wrap",
            gap: "0.5rem",
            fontSize: "0.85rem",
            color: "#9ca3af",
          }}
        >
          <span>
            <strong>Total events:</strong>{" "}
            {totalEvents.toLocaleString()}
          </span>
          {topEventType && (
            <span>
              <strong>Top type:</strong> {topEventType}
            </span>
          )}
          {clickCount !== null && (
            <span>
              <strong>Clicks in window:</strong>{" "}
              {clickCount.toLocaleString()}
            </span>
          )}
        </div>
      )}

      {loading && !data && !error && (
        <p className="card-text">Loading event-type metrics…</p>
      )}

      {error && (
        <p className="card-text card-text-error">{error}</p>
      )}

      {data && data.length > 0 && (
        <table className="metrics-table">
          <thead>
            <tr>
              <th>Event Type</th>
              <th style={{ textAlign: "right" }}>Count</th>
              <th style={{ textAlign: "right" }}>Share</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <tr key={idx}>
                <td>{row.event_type}</td>
                <td style={{ textAlign: "right" }}>
                  {row.count.toLocaleString()}
                </td>
                <td style={{ textAlign: "right" }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.35rem",
                      justifyContent: "flex-end",
                    }}
                  >
                    <span style={{ fontSize: "0.8rem", color: "#9ca3af" }}>
                      {formatShare(row.count)}
                    </span>
                    <div
                      style={{
                        width: "80px",
                        height: "6px",
                        borderRadius: "999px",
                        background: "#020617",
                        border: "1px solid #1f2937",
                        overflow: "hidden",
                      }}
                    >
                      <div
                        style={{
                          height: "100%",
                          width: barWidth(row.count),
                          borderRadius: "999px",
                          background:
                            "linear-gradient(to right, #22c55e, #22d3ee)",
                        }}
                      />
                    </div>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {!loading && !error && (!data || data.length === 0) && (
        <p className="card-text card-text-muted">
          No events in the selected window.
        </p>
      )}
    </section>
  );
};

export default EventTypeMetrics;
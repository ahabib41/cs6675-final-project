import React, { useEffect, useState } from "react";

const API_BASE = "http://localhost:8000";

type EventRow = {
  event_type?: string;
  user_id?: string;
  comment?: string | null;
  event_time?: string;
  ts?: string;
  timestamp?: string;
};

const RecentEvents: React.FC = () => {
  const [data, setData] = useState<EventRow[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const getTimeValue = (row: EventRow): string => {
    return (
      row.event_time ||
      row.ts ||
      row.timestamp ||
      "—"
    );
  };

  useEffect(() => {
    let cancelled = false;

    const fetchEvents = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/events/recent?limit=10`);
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `HTTP ${res.status}`);
        }
        const json = await res.json();
        if (!cancelled) {
          setData(json);
          setError(null);
          setLoading(false);
        }
      } catch (e: any) {
        if (!cancelled) {
          setError(e.message ?? "Failed to load recent events");
          setLoading(false);
        }
      }
    };

    fetchEvents(); // initial
    const id = setInterval(fetchEvents, 3000); // refresh every 3s

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  return (
    <section className="card">
      <h2 className="card-title">Recent Events</h2>

      {loading && !data && <p className="card-text">Loading…</p>}
      {error && <p className="card-text card-text-muted">{error}</p>}

      {data && data.length > 0 && (
        <table className="metrics-table">
          <thead>
            <tr>
              <th style={{ width: "30%" }}>Time</th>
              <th style={{ width: "20%" }}>Type</th>
              <th>Comment</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <tr key={idx}>
                <td style={{ fontSize: "0.8rem" }}>{getTimeValue(row)}</td>
                <td>{row.event_type || "—"}</td>
                <td style={{ fontSize: "0.9rem" }}>
                  {row.comment && row.comment.trim().length > 0
                    ? row.comment
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {!loading && !error && (!data || data.length === 0) && (
        <p className="card-text card-text-muted">
          No events yet — send one from the click panel.
        </p>
      )}
    </section>
  );
};

export default RecentEvents;
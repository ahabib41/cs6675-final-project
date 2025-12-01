import React, { useState } from "react";

const API_BASE = "http://localhost:8000";

const ClickPanel: React.FC = () => {
  const [comment, setComment] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const sendClick = async () => {
    setLoading(true);
    setStatus(null);
    try {
      const res = await fetch(`${API_BASE}/api/events/click`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_type: "click",
          user_id: "dashboard-user",
          comment: comment || null,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const json = await res.json();
      console.log("[ClickPanel] Response:", json);
      setStatus("Click event sent to backend & Kafka");
      setComment("");
    } catch (e: any) {
      setStatus(` Failed to send click: ${e.message ?? e}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card">
      <h2 className="card-title">Send Live Click Event</h2>
      <p className="card-text">
        This will send a <code>click</code> event to Kafka via the backend. As
        the streaming job ingests it, your event-type metrics will go up.
      </p>

      <label className="card-text" style={{ display: "block", marginBottom: 8 }}>
        Optional comment:
      </label>
      <textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        rows={3}
        style={{
          width: "100%",
          resize: "vertical",
          padding: "0.5rem",
          borderRadius: "0.5rem",
          border: "1px solid #374151",
          background: "#020617",
          color: "#e5e7eb",
          marginBottom: "0.75rem",
        }}
        placeholder="e.g. user clicked main CTA button"
      />

      <button
        onClick={sendClick}
        disabled={loading}
        style={{
          padding: "0.5rem 1.25rem",
          borderRadius: "999px",
          border: "none",
          background: loading ? "#6b7280" : "#22c55e",
          color: "#020617",
          fontWeight: 600,
          cursor: loading ? "default" : "pointer",
        }}
      >
        {loading ? "Sending…" : "Send Click Event"}
      </button>

      {status && (
        <p
          className="card-text"
          style={{ marginTop: "0.75rem", fontSize: "0.9rem" }}
        >
          {status}
        </p>
      )}
    </section>
  );
};

export default ClickPanel;
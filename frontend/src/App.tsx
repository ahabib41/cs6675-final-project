// src/App.tsx
import "./App.css";
import React from "react";

import HealthStatus from "./components/Health/HealthStatus";
import EventTypeMetrics from "./components/EventTypeMetrics";
import SummaryMetrics from "./components/SummaryMetrics";
import ClickPanel from "./components/ClickPanel";
import RecentEvents from "./components/RecentEvents";

function App() {
  return (
    <div className="app">
      <div className="app-container">
        <header className="app-header">
          <h1>Streaming Metrics Dashboard</h1>
        </header>

        <main className="app-main">
          {/* Left column */}
          <div className="app-column">
            <HealthStatus />
            <ClickPanel />
            <RecentEvents />
          </div>

          {/* Right column */}
          <div className="app-column">
            <EventTypeMetrics />
            <SummaryMetrics />
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
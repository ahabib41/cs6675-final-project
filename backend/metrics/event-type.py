from pathlib import Path
from typing import List, Dict

import pandas as pd
from fastapi import HTTPException, FastAPI

app = FastAPI(title="Streaming Metrics API")

BASE_DIR = Path(__file__).resolve().parents[2] 
DATA_DIR = BASE_DIR / "data"
METRICS_DIR = DATA_DIR / "metrics"
EVENT_TYPE_DIR = METRICS_DIR / "event_type_counts"
SUMMARY_DIR = METRICS_DIR / "summary"
TRUTH_EVENTS_DIR = DATA_DIR / "truth_events"  

@app.get("/api/metrics/event-type")
def get_event_type_metrics() -> List[Dict]:
    try:
        files = sorted(TRUTH_EVENTS_DIR.glob("*.parquet"))
        if not files:
            raise FileNotFoundError(f"No parquet files in {TRUTH_EVENTS_DIR}")

        # Read all micro-batches and stack them
        dfs = [pd.read_parquet(f) for f in files]
        df = pd.concat(dfs, ignore_index=True)

        if "event_type" not in df.columns:
            raise ValueError("Missing 'event_type' column in truth_events data")

        grouped = (
            df.groupby("event_type")
              .size()
              .reset_index(name="count")
              .sort_values("count", ascending=False)
        )

        return grouped.to_dict(orient="records")

    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Event-type metrics not ready yet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
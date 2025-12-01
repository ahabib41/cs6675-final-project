# backend/api/server.py

from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict
import logging
import json

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.kafka.api_producer import send_event as send_kafka_event

logger = logging.getLogger(__name__)

app = FastAPI(title="Streaming Metrics API")


# -------------------------
# Helpers
# -------------------------

def format_dt(dt):
    """
    Format various datetime inputs into 'YYYY-MM-DD HH:MM:SS'.
    Used mainly for display.
    """
    if dt is None:
        return None

    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            return dt  # fallback: return original string

    if not isinstance(dt, datetime):
        return str(dt)

    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)

    return dt.strftime("%Y-%m-%d %H:%M:%S")


# -------------------------
# CORS
# -------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# Paths / constants
# -------------------------

BASE_DIR = Path(__file__).resolve().parents[2]  # FINAL_PROJECT
DATA_DIR = BASE_DIR / "data"
METRICS_DIR = DATA_DIR / "metrics"
EVENT_TYPE_DIR = METRICS_DIR / "event_type_counts"
SUMMARY_DIR = METRICS_DIR / "summary"
TRUTH_EVENTS_DIR = DATA_DIR / "truth_events"

CLICK_EVENTS_PATH = DATA_DIR / "click_events.jsonl"
COMMENT_WINDOW_MINUTES = 5

class ClickEvent(BaseModel):
    event_type: str = "click"
    user_id: Optional[str] = None
    comment: Optional[str] = None


@app.post("/api/events/click")
def create_click_event(payload: ClickEvent):

    now_iso = datetime.utcnow().isoformat()

    event = {
        "event_type": payload.event_type,
        "user_id": payload.user_id or "web-dashboard",
        "comment": payload.comment,
        "event_time": now_iso,
        "ts": now_iso,
        "source": "dashboard",
    }

    logger.info(f"[CLICK] Received event: {event}")
    print(f"[CLICK] Received event: {event}")

    try:
        send_kafka_event(event)
    except Exception as e:
        logger.error(f"[CLICK] Failed to send to Kafka: {e}")
        raise HTTPException(status_code=500, detail="Failed to publish event")

    try:
        CLICK_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CLICK_EVENTS_PATH.open("a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as e:
        logger.error(f"[CLICK] Failed to append to {CLICK_EVENTS_PATH}: {e}")

    return {
        "status": "ok",
        "event": event,
    }


# -------------------------
# File helpers
# -------------------------

def _latest_file_info(dir_path: Path, pattern: str):
    """
    Return (exists, latest_filename, mtime_str) for a directory pattern.
    Used by /api/health to show latest batch files.
    """
    files = sorted(dir_path.glob(pattern))
    if not files:
        return False, None, None
    latest = files[-1]
    mtime = datetime.fromtimestamp(latest.stat().st_mtime).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    return True, latest.name, mtime


def _read_truth_events_all() -> pd.DataFrame:
    """
    Read ALL events from:
      - data/truth_events/*.parquet (Spark streaming)
      - data/click_events.jsonl    (dashboard clicks)
    and return one merged DataFrame.
    """
    frames: List[pd.DataFrame] = []

    # 1) Spark streaming truth_events
    truth_files = sorted(TRUTH_EVENTS_DIR.glob("*.parquet"))
    if truth_files:
        dfs = [pd.read_parquet(f) for f in truth_files]
        frames.append(pd.concat(dfs, ignore_index=True))

    # 2) Locally appended click events
    if CLICK_EVENTS_PATH.exists():
        click_df = pd.read_json(CLICK_EVENTS_PATH, lines=True)
        frames.append(click_df)

    if not frames:
        raise FileNotFoundError(
            f"No events found in {TRUTH_EVENTS_DIR} or {CLICK_EVENTS_PATH}"
        )

    return pd.concat(frames, ignore_index=True)


@app.get("/api/health")
def health():
    """
    Show backend status + last batch files produced for event-type and summary.
    (Even though summary metrics endpoint uses live events, we still
    show the batch summary parquet if present.)
    """
    event_ready, event_file, event_mtime = _latest_file_info(
        EVENT_TYPE_DIR, "*.parquet"
    )
    summary_ready, summary_file, summary_mtime = _latest_file_info(
        SUMMARY_DIR, "*.parquet"
    )

    return {
        "status": "ok",
        "event_type_metrics": {
            "ready": event_ready,
            "latest_file": event_file,
            "last_updated": event_mtime,
        },
        "summary_metrics": {
            "ready": summary_ready,
            "latest_file": summary_file,
            "last_updated": summary_mtime,
        },
    }


@app.get("/api/metrics/event-type")
def get_event_type_metrics(minutes: int = 0) -> List[Dict]:
    try:
        df = _read_truth_events_all()

        if "event_type" not in df.columns:
            raise ValueError("Missing 'event_type' column in events data")

        # Decide which column is the time column
        time_col = None
        for candidate in ["event_time", "ts", "timestamp"]:
            if candidate in df.columns:
                time_col = candidate
                break

        # Optional time filter: last N minutes
        if minutes > 0 and time_col:
            df[time_col] = pd.to_datetime(df[time_col], errors="coerce", utc=True)
            cutoff = pd.Timestamp.utcnow() - pd.Timedelta(minutes=minutes)
            df = df[df[time_col] >= cutoff]

        if df.empty:
            return []

        grouped = (
            df.groupby("event_type")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )

        return grouped.to_dict(orient="records")

    except FileNotFoundError:
        raise HTTPException(
            status_code=503, detail="Event-type metrics not ready yet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


@app.get("/api/metrics/summary")
def get_summary_metrics() -> List[Dict]:
    try:
        df = _read_truth_events_all()  

        if "event_time" not in df.columns:
            raise ValueError("Missing 'event_time' column in events data")
        if "user_id" not in df.columns:
            raise ValueError("Missing 'user_id' column in events data")

        df["event_time"] = pd.to_datetime(df["event_time"], errors="coerce", utc=True)
        df = df.dropna(subset=["event_time"])

        if df.empty:
            return []

        min_ts = df["event_time"].min()
        max_ts = df["event_time"].max()
        distinct_users = int(df["user_id"].nunique())
        total_events = int(df.shape[0])

        now_utc = pd.Timestamp.now(tz="UTC")
        recent_cutoff = now_utc - pd.Timedelta(minutes=5)
        events_last_5 = int(df[df["event_time"] >= recent_cutoff].shape[0])

        def fmt(ts):
            if isinstance(ts, pd.Timestamp):
                return ts.tz_convert("UTC").strftime("%Y-%m-%d %H:%M:%S")
            return str(ts)

        return [
            {"metric": "min_event_time", "value": fmt(min_ts)},
            {"metric": "max_event_time", "value": fmt(max_ts)},
            {"metric": "distinct_users", "value": distinct_users},
            {"metric": "total_events", "value": total_events},
            {"metric": "events_last_5_min", "value": events_last_5},
        ]

    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Summary metrics not ready yet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")

@app.get("/api/events/recent")
def get_recent_events(limit: int = 20) -> List[Dict]:

    try:
        df = _read_truth_events_all()

        # 1) Keep only rows that actually have a comment
        if "comment" in df.columns:
            df["comment"] = df["comment"].fillna("").astype(str)
            df = df[df["comment"].str.strip() != ""]
        else:
            return []

        if df.empty:
            return []

        # 2) Decide which column is the time column
        time_col = None
        for candidate in ["event_time", "ts", "timestamp"]:
            if candidate in df.columns:
                time_col = candidate
                break

        if time_col:
            df[time_col] = pd.to_datetime(df[time_col], errors="coerce", utc=True)

            cutoff = pd.Timestamp.utcnow() - pd.Timedelta(
                minutes=COMMENT_WINDOW_MINUTES
            )
            df = df[df[time_col] >= cutoff]

            if df.empty:
                return []

        cols = ["event_type", "user_id", "comment"]
        if time_col:
            cols.append(time_col)

        available_cols = [c for c in cols if c in df.columns]
        df_out = df[available_cols]

        if time_col and time_col in df_out.columns:
            df_out = df_out.sort_values(time_col, ascending=False).head(limit)
            df_out[time_col] = df_out[time_col].dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            df_out = df_out.tail(limit)

        return df_out.to_dict(orient="records")

    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="There is no events yet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
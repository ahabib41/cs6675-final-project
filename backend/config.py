from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

TRUTH_EVENTS_DIR = DATA_DIR / "truth_events"
METRICS_DIR = DATA_DIR / "metrics"
EVENT_TYPE_DIR = METRICS_DIR / "event_type_counts"
SUMMARY_DIR = METRICS_DIR / "summary"

KAFKA_BOOTSTRAP = "localhost:9092"
KAFKA_TOPIC = "viewer-events"

COMMENT_WINDOW_MINUTES = 3
#!/usr/bin/env bash
set -euo pipefail

echo "[backend] Moving to project root..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[backend] Starting Docker (Kafka, etc.)..."
if command -v docker-compose >/dev/null 2>&1; then
  docker-compose up -d
else
  docker compose up -d
fi

echo "[backend] Activating venv..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

if [ -f "requirements.txt" ]; then
  echo "[backend] Installing Python deps (if needed)..."
  pip install -r requirements.txt
fi

echo "[backend] Setting Java 17 for Spark..."
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
export PATH="$JAVA_HOME/bin:$PATH"

echo "[backend] Starting Spark streaming consumer in background..."
spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.13:3.5.0 \
  backend/streaming/consumer.py &

CONSUMER_PID=$!
echo "[backend] Streaming consumer PID: $CONSUMER_PID"
sleep 5

echo "[backend] Starting continuous Kafka producer in background..."
python -m backend.kafka.producer &

PRODUCER_PID=$!
echo "[backend] Producer PID: $PRODUCER_PID"

# Make sure metrics dirs exist
SUMMARY_DIR="$SCRIPT_DIR/data/metrics/summary"
EVENT_TYPE_DIR="$SCRIPT_DIR/data/metrics/event_type_counts"
mkdir -p "$SUMMARY_DIR" "$EVENT_TYPE_DIR"

echo "[backend] Checking for summary metrics in: $SUMMARY_DIR"
if ! ls "$SUMMARY_DIR"/*.parquet >/dev/null 2>&1; then
  echo "[backend] No summary parquet found -> running batch metrics job..."
  python backend/batch/compute_metrics.py
  echo "[backend] Batch metrics job completed."
else
  echo "[backend] Summary parquet already exists -> skipping batch metrics."
fi

echo "[backend] Starting FastAPI (Uvicorn)..."
uvicorn backend.api.server:app --host 0.0.0.0 --port 8000 --reload
#!/usr/bin/env bash
set -euo pipefail

cd /Users/antonyh/Desktop/FINAL_PROJECT

echo "[API] Activating venv..."
source .venv/bin/activate

echo "[API] Starting FastAPI server on http://localhost:8000 ..."
uvicorn backend.api.server:app --reload
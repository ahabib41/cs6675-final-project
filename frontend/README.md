# Streaming Metrics Dashboard

Small end-to-end project with:

- Kafka + Spark Structured Streaming (simulated viewer events)
- FastAPI backend (metrics + comments API)
- React frontend (live dashboard)

---

## 1. Setup (one time)

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate           # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

## 2. run the backend

sh run_backend.sh

## 3. run the frontend 
cd to frontend --> cd frontend
npm run dev 
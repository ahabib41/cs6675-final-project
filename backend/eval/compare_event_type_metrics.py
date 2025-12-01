# backend/eval/compare_event_type_metrics.py

import sys
from pathlib import Path

import pandas as pd


def main() -> None:
    """
    Compare:
      1) True event_type counts from data/truth_events
      2) Batch event_type counts from data/metrics/event_type_counts

    This is a small sanity-check script, not part of the API.
    """

    # Resolve paths relative to repo root
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    truth_events_dir = data_dir / "truth_events"
    metrics_dir = data_dir / "metrics"
    event_type_dir = metrics_dir / "event_type_counts"

    print("=== Event-Type Metrics Evaluation ===")
    print(f"Project root        : {project_root}")
    print(f"Truth events dir    : {truth_events_dir}")
    print(f"Batch metrics dir   : {event_type_dir}")
    print()

    # ---------- 1) Load truth_events ----------
    truth_files = sorted(truth_events_dir.glob("*.parquet"))
    if not truth_files:
        print(f"ERROR: no parquet files found in {truth_events_dir}")
        sys.exit(1)

    print(f"Found {len(truth_files)} truth_events parquet file(s).")

    truth_dfs = [pd.read_parquet(p) for p in truth_files]
    truth_df = pd.concat(truth_dfs, ignore_index=True)

    if "event_type" not in truth_df.columns:
        print("ERROR: 'event_type' column is missing in truth_events.")
        sys.exit(1)

    truth_counts = (
        truth_df.groupby("event_type")
        .size()
        .reset_index(name="true_count")
        .sort_values("true_count", ascending=False)
        .reset_index(drop=True)
    )

    print("\n--- True counts from data/truth_events ---")
    print(truth_counts.to_string(index=False))

    # ---------- 2) Load latest batch event_type_counts ----------
    metric_files = sorted(event_type_dir.glob("*.parquet"))
    if not metric_files:
        print(f"\nERROR: no parquet files found in {event_type_dir}")
        sys.exit(1)

    latest_metric_file = metric_files[-1]
    print(f"\nUsing batch metrics file: {latest_metric_file.name}")

    batch_df = pd.read_parquet(latest_metric_file)

    if "event_type" not in batch_df.columns or "count" not in batch_df.columns:
        print("ERROR: 'event_type' or 'count' column missing in batch metrics.")
        sys.exit(1)

    batch_counts = (
        batch_df[["event_type", "count"]]
        .rename(columns={"count": "batch_count"})
        .sort_values("batch_count", ascending=False)
        .reset_index(drop=True)
    )

    print("\n--- Batch counts from data/metrics/event_type_counts ---")
    print(batch_counts.to_string(index=False))

    # ---------- 3) Join and compare ----------
    merged = pd.merge(
        truth_counts,
        batch_counts,
        on="event_type",
        how="outer",
        indicator=True,
    )

    merged["true_count"] = merged["true_count"].fillna(0).astype(int)
    merged["batch_count"] = merged["batch_count"].fillna(0).astype(int)
    merged["abs_diff"] = (merged["batch_count"] - merged["true_count"]).abs()

    merged = merged.sort_values("true_count", ascending=False).reset_index(drop=True)

    print("\n--- Comparison (true vs batch) ---")
    print(
        merged[
            ["event_type", "true_count", "batch_count", "abs_diff", "_merge"]
        ].to_string(index=False)
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
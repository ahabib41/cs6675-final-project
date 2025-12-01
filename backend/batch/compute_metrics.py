import os
import traceback
from pathlib import Path

from pyspark.sql import SparkSession, functions as F

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
TRUTH_EVENTS_DIR = DATA_DIR / "truth_events"
METRICS_DIR = DATA_DIR / "metrics"
EVENT_TYPE_DIR = METRICS_DIR / "event_type_counts"
SUMMARY_DIR = METRICS_DIR / "summary"


def main():
    spark = None
    try:
        os.makedirs(EVENT_TYPE_DIR, exist_ok=True)
        os.makedirs(SUMMARY_DIR, exist_ok=True)

        # Start Spark
        spark = (
            SparkSession.builder
            .appName("compute_metrics")
            .master("local[*]")  
            .getOrCreate()
        )

        print(f"METRICS Reading truth_events from {TRUTH_EVENTS_DIR} ...")
        df = spark.read.parquet(str(TRUTH_EVENTS_DIR))

        print("METRICS Schema:")
        df.printSchema()

        # 2) Event-type counts
        event_counts = (
            df.groupBy("event_type")
              .agg(F.count("*").alias("count"))
              .orderBy("event_type")
        )

        print("\nMETRICS Event type counts:")
        event_counts.show(truncate=False)

        users = df.select("user_id").distinct().count()
        print(f"\nMETRICS Distinct users: {users}")

        # 4) Time range
        time_range = df.agg(
            F.min("event_time").alias("min_event_time"),
            F.max("event_time").alias("max_event_time"),
        )
        print("\nMETRICS Event time range:")
        time_range.show(truncate=False)

        print("\nMETRICS Writing outputs to data/metrics ...")

        event_counts.write.mode("overwrite").parquet(str(EVENT_TYPE_DIR))
        print(f"METRICS Wrote event_type_counts to {EVENT_TYPE_DIR}")

        summary = time_range.withColumn("distinct_users", F.lit(users))
        summary.write.mode("overwrite").parquet(str(SUMMARY_DIR))
        print(f"METRICS Wrote summary metrics to {SUMMARY_DIR}")

        print("METRICS is Done computing metrics.")

    except Exception as e:
        print("METRICS Error while computing metrics:")
        print(e)
        traceback.print_exc()
        raise
    finally:
        if spark is not None:
            spark.stop()
            print("METRICS SparkSession stopped.")


if __name__ == "__main__":
    main()
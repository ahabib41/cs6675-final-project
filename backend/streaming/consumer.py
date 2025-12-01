# backend/streaming/consumer.py

from pathlib import Path

from pyspark.sql import SparkSession, functions as F
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    TimestampType,
)

KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC_NAME = "viewer-events" 

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
TRUTH_EVENTS_DIR = DATA_DIR / "truth_events"
CHECKPOINT_DIR = DATA_DIR / "checkpoints" / "truth_events"


def create_spark() -> SparkSession:
    spark = (
        SparkSession.builder
        .appName("ViewerEventsStreamingConsumer")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark


def get_event_schema() -> StructType:

    return StructType(
        [
            StructField("stream_id", StringType(), True),
            StructField("user_id", StringType(), True),
            StructField("tab_id", StringType(), True),
            StructField("event_type", StringType(), True),
            StructField("event_time", TimestampType(), True),
            StructField("receive_time", TimestampType(), True),
            StructField("event_id", StringType(), True),

            # from dashboard clicks
            StructField("comment", StringType(), True),
            StructField("ts", StringType(), True),
            StructField("source", StringType(), True),
        ]
    )


def write_batch_to_parquet(batch_df, batch_id: int):
    if batch_df.rdd.isEmpty():
        return

    batch_df = batch_df.withColumn(
        "event_time",
        F.coalesce(
            col("event_time"),
            F.to_timestamp(col("ts"))
        ),
    )

    # Ensure directory exists
    TRUTH_EVENTS_DIR.mkdir(parents=True, exist_ok=True)

    # Append micro-batch to parquet
    (
        batch_df
        .write
        .mode("append")
        .parquet(str(TRUTH_EVENTS_DIR))
    )

    # Optional: log event_type counts for visibility
    counts = (
        batch_df.groupBy("event_type")
        .count()
        .orderBy(F.col("count").desc())
    )
    print(f"[STREAM] Batch {batch_id} written to {TRUTH_EVENTS_DIR}")
    counts.show(truncate=False)


def main():
    spark = create_spark()
    schema = get_event_schema()

    raw_df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", TOPIC_NAME)
        .option("startingOffsets", "earliest")
        .load()
    )

    parsed = raw_df.select(
        from_json(col("value").cast("string"), schema).alias("e")
    )
    events = parsed.select("e.*")

    query = (
        events.writeStream
        .outputMode("append")
        .option("checkpointLocation", str(CHECKPOINT_DIR))
        .foreachBatch(write_batch_to_parquet)
        .start()
    )

    query.awaitTermination()


if __name__ == "__main__":
    main()
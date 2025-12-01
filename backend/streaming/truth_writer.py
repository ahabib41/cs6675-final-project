from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    TimestampType,
)

KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC_NAME = "viewer-events"
OUTPUT_PATH = "data/truth_events"
CHECKPOINT_PATH = "checkpoints/truth_writer"


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
        ]
    )


def create_spark() -> SparkSession:
    spark = (
        SparkSession.builder
        .appName("ViewerEventsTruthWriter")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark


def run_truth_writer() -> None:
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
        from_json(col("value").cast("string"), schema).alias("e"),
        current_timestamp().alias("processing_time"),
    )

    events = parsed.select("e.*", "processing_time")

    query = (
        events.writeStream
        .outputMode("append")
        .format("parquet")
        .option("path", OUTPUT_PATH)
        .option("checkpointLocation", CHECKPOINT_PATH)
        .start()
    )

    query.awaitTermination()


def main() -> None:
    try:
        print("[INFO] Starting truth_writer...")
        run_truth_writer()
    except Exception as exc:
        print("[ERROR] truth_writer main:", repr(exc))
        raise


if __name__ == "__main__":
    main()
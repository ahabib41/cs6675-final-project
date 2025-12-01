# backend/kafka/api_producer.py
import json
import os
from typing import Dict, Any

from confluent_kafka import Producer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "page_events")  


producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP})


def _delivery_report(err, msg):
    if err is not None:
        print(f"API-KAFKA Delivery failed: {err}")
    else:
        print(
            f"API-KAFKA Delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}"
        )


def send_event(event: Dict[str, Any]) -> None:
    payload = json.dumps(event).encode("utf-8")
    producer.produce(KAFKA_TOPIC, value=payload, callback=_delivery_report)
    producer.poll(0)
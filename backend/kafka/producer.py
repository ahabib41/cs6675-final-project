import json
import random
import time
from datetime import datetime, timedelta
from uuid import uuid4

from confluent_kafka import Producer

KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC_NAME = "viewer-events"


def make_producer() -> Producer:
    return Producer({"bootstrap.servers": KAFKA_BOOTSTRAP})


def _random_user_id() -> str:
    return f"user-{random.randint(1, 500)}"


def _random_stream_id() -> str:
    return f"stream-{random.randint(1, 20)}"


def generate_session_events() -> list[dict]:

    stream_id = _random_stream_id()
    user_id = _random_user_id()
    base_time = datetime.utcnow()

    events = []

    events.append(
        {
            "stream_id": stream_id,
            "user_id": user_id,
            "tab_id": "main",
            "event_type": "start",
            "event_time": base_time.isoformat(),
            "receive_time": base_time.isoformat(),
            "event_id": str(uuid4()),
        }
    )

    hb_count = random.randint(3, 8)
    for i in range(hb_count):
        t = base_time + timedelta(seconds=5 * (i + 1))
        events.append(
            {
                "stream_id": stream_id,
                "user_id": user_id,
                "tab_id": "main",
                "event_type": "heartbeat",
                "event_time": t.isoformat(),
                "receive_time": t.isoformat(),
                "event_id": str(uuid4()),
            }
        )

    # end
    end_time = base_time + timedelta(seconds=5 * (hb_count + 1))
    events.append(
        {
            "stream_id": stream_id,
            "user_id": user_id,
            "tab_id": "main",
            "event_type": "end",
            "event_time": end_time.isoformat(),
            "receive_time": end_time.isoformat(),
            "event_id": str(uuid4()),
        }
    )

    return events


def send_events_forever():
    producer = make_producer()

    try:
        while True:
            sessions = random.randint(3, 7)
            batch = []

            for _ in range(sessions):
                batch.extend(generate_session_events())

            for event in batch:
                payload = json.dumps(event).encode("utf-8")
                producer.produce(TOPIC_NAME, value=payload)

            producer.poll(0)
            producer.flush()

            print(
                f"[PRODUCER] Sent {len(batch)} events "
                f"(sessions={sessions}) at {datetime.utcnow().isoformat(timespec='seconds')}Z"
            )

            # small pause so it's not crazy fast
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nproducer Stopped by user.")
    finally:
        try:
            producer.flush()
        except Exception:
            pass
        print("producer Shutdown complete.")


def main():
    send_events_forever()


if __name__ == "__main__":
    main()
from datetime import datetime, timedelta
import traceback

from .models import ScenarioConfig
from .generator import generate_session_events


def debug_once():
    try:
        cfg = ScenarioConfig(
            name="debug",
            num_streams=1,
            num_viewers=1,
            session_min_minutes=1,
            session_max_minutes=1,
        )
        now = datetime.utcnow()
        events = generate_session_events(
            stream_id="debug-stream",
            user_id="debug-user",
            tab_id="tab-1",
            start_time=now,
            duration=timedelta(minutes=1),
            cfg=cfg,
        )
        print(f"Generated {len(events)} events:")
        for ev in events:
            print(ev.to_json())
    except Exception as e:
        print("error debug_once:", e)
        traceback.print_exc()
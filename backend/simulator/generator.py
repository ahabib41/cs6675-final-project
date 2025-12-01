from datetime import datetime, timedelta
from typing import List
import random, uuid, traceback

from .models import ViewerEvent, ScenarioConfig


def generate_session_events(
    stream_id: str,
    user_id: str,
    tab_id: str,
    start_time: datetime,
    duration: timedelta,
    cfg: ScenarioConfig,
) -> List[ViewerEvent]:
    try:
        events: List[ViewerEvent] = []
        events.append(
            ViewerEvent(
                stream_id=stream_id,
                user_id=user_id,
                tab_id=tab_id,
                event_type="start",
                event_time=start_time,
                receive_time=start_time,
                event_id=str(uuid.uuid4()),
            )
        )
        heartbeat_time = start_time + timedelta(seconds=cfg.heartbeat_interval_seconds)
        end_time = start_time + duration
        while heartbeat_time < end_time:
            events.append(
                ViewerEvent(
                    stream_id=stream_id,
                    user_id=user_id,
                    tab_id=tab_id,
                    event_type="heartbeat",
                    event_time=heartbeat_time,
                    receive_time=heartbeat_time,
                    event_id=str(uuid.uuid4()),
                )
            )
            heartbeat_time += timedelta(seconds=cfg.heartbeat_interval_seconds)
        if random.random() > cfg.missing_end_probability:
            events.append(
                ViewerEvent(
                    stream_id=stream_id,
                    user_id=user_id,
                    tab_id=tab_id,
                    event_type="end",
                    event_time=end_time,
                    receive_time=end_time,
                    event_id=str(uuid.uuid4()),
                )
            )
        final_events: List[ViewerEvent] = []
        for ev in events:
            receive_time = ev.receive_time
            if random.random() < cfg.late_event_probability:
                receive_time += timedelta(seconds=random.randint(5, 40))
            new_ev = ViewerEvent(
                stream_id=ev.stream_id,
                user_id=ev.user_id,
                tab_id=ev.tab_id,
                event_type=ev.event_type,
                event_time=ev.event_time,
                receive_time=receive_time,
                event_id=ev.event_id,
            )
            final_events.append(new_ev)
            if random.random() < cfg.duplicate_probability:
                dup = ViewerEvent(
                    stream_id=new_ev.stream_id,
                    user_id=new_ev.user_id,
                    tab_id=new_ev.tab_id,
                    event_type=new_ev.event_type,
                    event_time=new_ev.event_time,
                    receive_time=new_ev.receive_time
                    + timedelta(milliseconds=random.randint(10, 500)),
                    event_id=new_ev.event_id,
                )
                final_events.append(dup)
        final_events.sort(key=lambda e: e.receive_time)
        return final_events
    except Exception as e:
        print("[ERROR] generate_session_events:", e)
        traceback.print_exc()
        raise


def generate_scenario_events(cfg: ScenarioConfig) -> List[ViewerEvent]:
    """Events for many viewers in a scenario."""
    try:
        base_time = datetime.utcnow()
        all_events: List[ViewerEvent] = []
        for i in range(cfg.num_viewers):
            stream_id = f"stream-{i % cfg.num_streams + 1}"
            user_id = f"user-{i}"
            tab_id = "tab-1"
            start = base_time + timedelta(seconds=random.randint(0, 30))
            minutes = random.randint(cfg.session_min_minutes, cfg.session_max_minutes)
            duration = timedelta(minutes=minutes)
            session_events = generate_session_events(
                stream_id=stream_id,
                user_id=user_id,
                tab_id=tab_id,
                start_time=start,
                duration=duration,
                cfg=cfg,
            )
            all_events.extend(session_events)
        all_events.sort(key=lambda e: e.receive_time)
        return all_events
    except Exception as e:
        print("error generate_scenario_events:", e)
        traceback.print_exc()
        raise
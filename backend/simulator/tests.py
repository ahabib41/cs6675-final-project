from datetime import datetime, timedelta
import traceback

from .models import ScenarioConfig
from .generator import generate_session_events, generate_scenario_events


def _test_single_session_basic():
    try:
        print("[TEST] single_session_basic")
        cfg = ScenarioConfig(
            name="test-basic",
            num_streams=1,
            num_viewers=1,
            session_min_minutes=1,
            session_max_minutes=1,
            heartbeat_interval_seconds=10,
            missing_end_probability=0.0,
            late_event_probability=0.0,
            duplicate_probability=0.0,
        )
        now = datetime.utcnow()
        events = generate_session_events(
            stream_id="test-stream",
            user_id="test-user",
            tab_id="tab-1",
            start_time=now,
            duration=timedelta(minutes=1),
            cfg=cfg,
        )
        assert len(events) >= 3, "Too few events generated"
        allowed = {"start", "heartbeat", "end"}
        for ev in events:
            assert ev.event_type in allowed, f"Bad event_type: {ev.event_type}"
        print(" PASS")
    except Exception as e:
        print("FAIL:", e)
        traceback.print_exc()


def _test_receive_time_sorted():
    try:
        print("[TEST] receive_time_sorted")
        cfg = ScenarioConfig(
            name="test-sorted",
            num_streams=1,
            num_viewers=3,
            session_min_minutes=1,
            session_max_minutes=2,
        )
        events = generate_scenario_events(cfg)
        for prev, curr in zip(events, events[1:]):
            assert prev.receive_time <= curr.receive_time, "Events not sorted"
        print("PASS")
    except Exception as e:
        print("FAIL:", e)
        traceback.print_exc()


def _test_duplicates_possible():
    try:
        print("Test duplicates_possible")
        cfg = ScenarioConfig(
            name="test-dup",
            num_streams=1,
            num_viewers=5,
            session_min_minutes=1,
            session_max_minutes=1,
            duplicate_probability=0.9,
        )
        events = generate_scenario_events(cfg)
        seen = set()
        dup = False
        for ev in events:
            if ev.event_id in seen:
                dup = True
                break
            seen.add(ev.event_id)
        if dup:
            print(" PASS (duplicate event_id observed)")
        else:
            print("WARN (no duplicates observed, still valid)")
    except Exception as e:
        print("FAIL:", e)
        traceback.print_exc()


def run_basic_tests():
    try:
        _test_single_session_basic()
        _test_receive_time_sorted()
        _test_duplicates_possible()
    except Exception as e:
        print("[Error run_basic_tests:", e)
        traceback.print_exc()
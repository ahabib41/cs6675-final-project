from typing import List
import traceback

from .models import ScenarioConfig, ViewerEvent
from .generator import generate_scenario_events
from .tests import run_basic_tests
from .debug import debug_once


def run_easy_scenario() -> List[ViewerEvent]:
    try:
        cfg = ScenarioConfig(
            name="easy",
            num_streams=1,
            num_viewers=5,
            session_min_minutes=1,
            session_max_minutes=3,
        )
        return generate_scenario_events(cfg)
    except Exception as e:
        print("Error run_easy_scenario:", e)
        traceback.print_exc()
        raise


def main():
    try:
        run_basic_tests()
        debug_once()
        events = run_easy_scenario()
        for ev in events:
            print(ev.to_json())
    except Exception as e:
        print("Error main in runner:", e)
        traceback.print_exc()


if __name__ == "__main__":
    main()
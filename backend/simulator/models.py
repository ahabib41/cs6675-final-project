from dataclasses import dataclass, asdict
from datetime import datetime
import json
import traceback


@dataclass
class ViewerEvent:
    stream_id: str
    user_id: str
    tab_id: str
    event_type: str  # "start" | "heartbeat" | "end"
    event_time: datetime
    receive_time: datetime
    event_id: str

    def to_dict(self) -> dict:
        try:
            d = asdict(self)
            d["event_time"] = self.event_time.isoformat()
            d["receive_time"] = self.receive_time.isoformat()
            return d
        except Exception as e:
            print("Error ViewerEvent.to_dict:", e)
            traceback.print_exc()
            raise

    def to_json(self) -> str:
        try:
            return json.dumps(self.to_dict(), separators=(",", ":"))
        except Exception as e:
            print("Error ViewerEvent.to_json:", e)
            traceback.print_exc()
            raise


@dataclass
class ScenarioConfig:
    name: str
    num_streams: int
    num_viewers: int
    session_min_minutes: int
    session_max_minutes: int
    heartbeat_interval_seconds: int = 5
    missing_end_probability: float = 0.05
    late_event_probability: float = 0.05
    duplicate_probability: float = 0.01
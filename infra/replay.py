"""
Replay Recording System.

Saves complete tick-by-tick sensor input and motor output for deterministic
replay, debugging, and analysis.
"""

"""
Replay Recording System.

Saves complete tick-by-tick sensor input, motor output, and cognitive state 
for deterministic replay, debugging, and analysis.
"""

from infra.json import BIOSJsonEncoder
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
import json


@dataclass(slots=True)
class ReplayFrame:
    tick: int
    sensor_packet: Dict[str, Any]
    motor_output: Dict[str, Any]
    goal_name: Optional[str] = None
    goal_priority: Optional[float] = None
    active_skill: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    target_x: Optional[float] = None
    target_y: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ReplayRecorder:

    def __init__(self, path="replay.jsonl"):
        self.file = open(path, "a+", encoding="utf-8")

    def record(self, frame: ReplayFrame):
        self.file.write(json.dumps(frame, cls=BIOSJsonEncoder) + "\n")

    def close(self):
        self.file.close()

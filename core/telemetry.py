from dataclasses import dataclass, asdict
from typing import Dict, Any
import json
import time


@dataclass(slots=True)
class TickTelemetry:
    tick: int

    energy: float
    integrity: float

    stress: float
    fear: float
    drive: float

    thrust: float
    steer: float

    pos_x: float
    pos_y: float

    velocity_x: float
    velocity_y: float

    landmark_count: int
    grid_cells: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TelemetryRecorder:

    def __init__(self, path: str = "telemetry.jsonl"):

        self.path = path

        self.file = open(path, "a", encoding="utf-8")

    def record(self, data: TickTelemetry):

        self.file.write(
            json.dumps(data.to_dict()) + "\n"
        )

    def close(self):

        self.file.close()
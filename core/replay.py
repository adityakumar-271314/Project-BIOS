from dataclasses import dataclass, asdict
from typing import Dict, Any
import json


@dataclass(slots=True)
class ReplayFrame:

    tick: int

    sensor_packet: Dict[str, Any]

    motor_output: Dict[str, Any]

    def to_dict(self):

        return asdict(self)


class ReplayRecorder:

    def __init__(self, path="replay.jsonl"):

        self.file = open(path, "a", encoding="utf-8")

    def record(self, frame: ReplayFrame):

        self.file.write(
            json.dumps(frame.to_dict()) + "\n"
        )

    def close(self):

        self.file.close()
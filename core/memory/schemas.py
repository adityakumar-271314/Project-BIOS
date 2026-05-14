from dataclasses import dataclass

@dataclass
class EpisodicEvent:

    tick: int

    event_type: str

    significance: float

    pos_x: float
    pos_y: float

    energy: float
    integrity: float

    stress: float
    fear: float
    drive: float
from dataclasses import dataclass

@dataclass(slots=True)
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

    energy_delta: float
    integrity_delta: float
    stress_delta: float
    fear_delta: float
    drive_delta: float

    def to_dict(self):

        return {
            "tick": self.tick,
            "event_type": self.event_type,
            "significance": self.significance,

            "position": {
                "x": self.pos_x,
                "y": self.pos_y,
            },

            "state": {
                "energy": self.energy,
                "integrity": self.integrity,
                "stress": self.stress,
                "fear": self.fear,
                "drive": self.drive,
            },

            "deltas": {
                "energy_delta": self.energy_delta,
                "integrity_delta": self.integrity_delta,
                "stress_delta": self.stress_delta,
                "fear_delta": self.fear_delta,
                "drive_delta": self.drive_delta,
            },
        }

    @classmethod
    def from_dict(cls, data: dict):

        state = data["state"]
        deltas = data["deltas"]
        pos = data["position"]

        return cls(
            tick=data["tick"],
            event_type=data["event_type"],
            significance=data["significance"],

            pos_x=pos["x"],
            pos_y=pos["y"],

            energy=state["energy"],
            integrity=state["integrity"],
            stress=state["stress"],
            fear=state["fear"],
            drive=state["drive"],

            energy_delta=deltas["energy_delta"],
            integrity_delta=deltas["integrity_delta"],
            stress_delta=deltas["stress_delta"],
            fear_delta=deltas["fear_delta"],
            drive_delta=deltas["drive_delta"],
        )

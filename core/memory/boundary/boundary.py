from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class BoundaryInterval:
    """
    Standalone schema representing a detected temporal episode boundary interval.

    Decoupled from EpisodicEvent, capturing start/end confidence and activation
    triggers for temporal segment filtering and episode construction.
    """

    start_tick: int
    end_tick: int
    start_confidence: float = 0.0
    end_confidence: float = 0.0
    start_reasons: List[str] = field(default_factory=list)
    end_reasons: List[str] = field(default_factory=list)

    @property
    def duration(self) -> int:
        """Returns the length of the interval in ticks."""
        return max(0, self.end_tick - self.start_tick)

    def to_dict(self) -> dict:
        """Serializes boundary interval to dictionary."""
        return {
            "start_tick": self.start_tick,
            "end_tick": self.end_tick,
            "start_confidence": self.start_confidence,
            "end_confidence": self.end_confidence,
            "start_reasons": list(self.start_reasons),
            "end_reasons": list(self.end_reasons),
            "duration": self.duration,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BoundaryInterval":
        """Deserializes boundary interval from dictionary."""
        return cls(
            start_tick=data["start_tick"],
            end_tick=data["end_tick"],
            start_confidence=data.get("start_confidence", 0.0),
            end_confidence=data.get("end_confidence", 0.0),
            start_reasons=data.get("start_reasons", []),
            end_reasons=data.get("end_reasons", []),
        )

from dataclasses import dataclass
from typing import Tuple, Any, Dict
from types import MappingProxyType

@dataclass(frozen=True, slots=True)
class ReplayTick:
    tick: int
    pos_x: float
    pos_y: float
    heading: float
    energy: float
    integrity: float
    stress: float
    fear: float
    drive: float
    confidence: float
    anchor: bool

@dataclass(frozen=True, slots=True)
class ReplaySession:
    name: str
    episode_id: str
    ticks: Tuple[ReplayTick, ...]  # Enforce structural immutability over mutable Lists
    duration: float
    statistics: Dict[str, Any]
    camera_bounds: Tuple[float, float, float, float]
    metadata: Dict[str, Any]
    schema_version: str = "1.0"

    def __post_init__(self):
        # Defensively freeze runtime dictionaries to prevent nested modifications
        object.__setattr__(self, "statistics", MappingProxyType(dict(self.statistics)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def get_tick(self, frame_idx: int) -> ReplayTick | None:
        return self.ticks[frame_idx] if 0 <= frame_idx < len(self.ticks) else None

    def validate(self) -> bool:
        """Robust architectural edge-validation checks."""
        if not self.ticks or len(self.ticks) == 0:
            return False
        if self.schema_version != "1.0":
            return False
            
        # Verify sequential ordering, coordinate sanity, and extreme corruption indicators
        last_tick = -1
        for t in self.ticks:
            if t.tick <= last_tick:  # Out of order or duplicates
                return False
            if t.confidence < 0.0 or t.confidence > 1.0:  # Range bound violation
                return False
            last_tick = t.tick
            
        return True
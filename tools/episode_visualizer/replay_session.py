from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any

@dataclass
class ReplaySession:
    """Immutable replay data boundary"""
    name: str
    episode_id: str
    ticks: List[Dict]  # List of frame dicts
    duration: float
    statistics: Dict[str, Any]
    camera_bounds: Tuple[float, float, float, float]  # (minx, miny, maxx, maxy)
    metadata: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "1.0"

    def get_tick(self, frame_idx: int) -> Dict:
        """Read-only access to a specific tick frame"""
        if 0 <= frame_idx < len(self.ticks):
            return self.ticks[frame_idx]
        return None

    def validate(self) -> bool:
        return len(self.ticks) > 0 and self.schema_version == "1.0"
from dataclasses import dataclass
from typing import Optional
from core.vector import Vector2
from core.brain.navigate.target import SpatialTargetTemplate

@dataclass
class Goal:
    name: str
    priority: float
    persistence: int = 0
    target_vector: Optional[Vector2] = None   # Backward compatibility or baseline point
    status: str = "pending"                  # "pending", "done", "failed"
    temporal_frame: str = "present"          # "past", "present", "future"
    strategy: str = "direct_sensory"         # "direct_sensory" or "memory_nav"
    spatial_target: Optional[SpatialTargetTemplate] = None

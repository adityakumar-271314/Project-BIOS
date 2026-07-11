from dataclasses import dataclass, field
from typing import Optional
from core.vector import Vector2


@dataclass
class SpatialTargetTemplate:
    """A baseline structural tracking container for spatial destination updates."""

    target_vector: Vector2
    hysteresis_radius: Optional[float] = None
    velocity: Optional[Vector2] = None
    confidence: float = 1.0  # Range: [0.0, 1.0] scales up/down on completion parameters
    metadata: dict = field(default_factory=dict)

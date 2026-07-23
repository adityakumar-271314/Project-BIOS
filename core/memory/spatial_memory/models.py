from __future__ import annotations
from dataclasses import dataclass
from core.vector import Vector2


@dataclass
class LandmarkRecord:
    """Everything the agent remembers about a named object."""

    pos: Vector2  # Estimated world-frame position
    last_seen_tick: int = 0
    observation_count: int = 1


@dataclass
class GridCell:
    """A single cell in the sparse trauma/bounty grid."""

    hazard: float = 0.0  # Accumulated hazard intensity (0–1)
    food: float = 0.0  # Accumulated food intensity   (0–1)
    last_updated_tick: int = 0

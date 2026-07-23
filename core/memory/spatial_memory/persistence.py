from __future__ import annotations
import json
import os
from pathlib import Path
from core.vector import Vector2
from .models import LandmarkRecord, GridCell


class PersistenceManager:
    """Manages reading and writing state to disk."""

    @staticmethod
    def export_state(
        tick: int, pos: Vector2, vel: Vector2, landmarks: dict, grid: dict
    ) -> dict:
        return {
            "tick": tick,
            "position": {"x": pos.x, "y": pos.y},
            "velocity": {"x": vel.x, "y": vel.y},
            "landmarks": {
                str(k): {
                    "x": v.pos.x,
                    "y": v.pos.y,
                    "last_seen_tick": v.last_seen_tick,
                    "observation_count": v.observation_count,
                }
                for k, v in landmarks.items()
            },
            "grid": {
                f"{cx},{cy}": {
                    "hazard": cell.hazard,
                    "food": cell.food,
                    "last_updated_tick": cell.last_updated_tick,
                }
                for (cx, cy), cell in grid.items()
            },
        }

    @staticmethod
    def save_to_disk(state: dict, storage_path: str) -> None:
        file_path = Path(storage_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)
        print(f"Semantic memory state saved to {file_path.resolve()}")

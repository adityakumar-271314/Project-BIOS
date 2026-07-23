from __future__ import annotations
import os
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
from core.vector import Vector2
from infra.data_models import SensorPacket

from .models import LandmarkRecord, GridCell
from .odometry import OdometryTracker
from .landmark_tracker import LandmarkTracker
from .stimulus_grid import StimulusGrid
from .persistence import PersistenceManager


class SpatialMemory:
    """Unified Facade orchestrating Spatial Subsystems."""

    def __init__(self, config) -> None:
        self.cfg = config
        self._tick: int = 0

        self._odometry = OdometryTracker()
        self._landmark_tracker = LandmarkTracker(config)
        self._stimulus_grid = StimulusGrid(config)
        self._cell_size: float = self.cfg.cell_size

    @property
    def internal_pos(self) -> Vector2:
        return self._odometry.pos

    @internal_pos.setter
    def internal_pos(self, value: Vector2):
        self._odometry.pos = value

    @property
    def internal_vel(self) -> Vector2:
        return self._odometry.vel

    @internal_vel.setter
    def internal_vel(self, value: Vector2) -> None:
        self._odometry.vel = value

    @property
    def internal_heading(self) -> float:
        return self._odometry.heading

    @property
    def _landmarks(self) -> Dict[int, LandmarkRecord]:
        return self._landmark_tracker.landmarks

    @property
    def _grid(self) -> Dict[Tuple[int, int], GridCell]:
        return self._stimulus_grid.grid

    def update(self, sensors: SensorPacket) -> None:
        self._tick += 1
        self._odometry.integrate(sensors, sensors.delta)

        self.internal_pos = self._landmark_tracker.process(
            sensors, self.internal_pos, self._tick
        )

        self._stimulus_grid.record(sensors, self.internal_pos, self._tick)
        self._stimulus_grid.decay()

    def get_spatial_bias(
        self, position: Optional[Vector2] = None, radius: Optional[float] = None
    ) -> Vector2:
        pos = position if position is not None else self.internal_pos
        rad = radius if radius is not None else self.cfg.bias_radius
        return self._stimulus_grid.compute_bias(pos, rad)

    @property
    def position(self) -> Vector2:
        return self.internal_pos.copy()

    @property
    def velocity(self) -> Vector2:
        return self.internal_vel.copy()

    @property
    def landmarks(self) -> Dict[int, LandmarkRecord]:
        return self._landmarks

    def get_cell(self, world_pos: Vector2) -> Optional[GridCell]:
        return self._grid.get(self._stimulus_grid.world_to_cell(world_pos))

    def debug_summary(self) -> str:
        return (
            f"[tick={self._tick}] pos={self.internal_pos} "
            f"vel={self.internal_vel} "
            f"landmarks={len(self._landmarks)} "
            f"grid_cells={len(self._grid)}"
        )

    def import_state(self, data: dict) -> None:
        self._tick = data.get("tick", 0)

        pos = data.get("position", {})
        self.internal_pos = Vector2(pos.get("x", 0.0), pos.get("y", 0.0))

        vel = data.get("velocity", {})
        self._odometry.vel = Vector2(vel.get("x", 0.0), vel.get("y", 0.0))

        self._landmark_tracker.clear()
        for obj_id, lm in data.get("landmarks", {}).items():
            self._landmarks[int(obj_id)] = LandmarkRecord(
                pos=Vector2(lm["x"], lm["y"]),
                last_seen_tick=lm["last_seen_tick"],
                observation_count=lm["observation_count"],
            )

        self._stimulus_grid.clear()
        for key, cell in data.get("grid", {}).items():
            cx, cy = map(int, key.split(","))
            self._grid[(cx, cy)] = GridCell(
                hazard=cell["hazard"],
                food=cell["food"],
                last_updated_tick=cell["last_updated_tick"],
            )

    def export_state(self) -> dict:
        return PersistenceManager.export_state(
            self._tick,
            self.internal_pos,
            self.internal_vel,
            self._landmarks,
            self._grid,
        )

    def initialize_run_state(
        self,
        continuation: bool,
        storage_path: str = "spatial_memory_state.json",
        episodes_dir: Path | str | None = None,
    ) -> None:
        if continuation and os.path.exists(storage_path):
            try:
                with open(storage_path, "r", encoding="utf-8") as f:
                    self.import_state(json.load(f))
                return
            except Exception:
                print("Saved memory state corrupt. Re-initializing...")

        self.reset_state(storage_path)

    def shutdown_and_save(
        self, storage_path: str = "spatial_memory_state.json"
    ) -> None:
        PersistenceManager.save_to_disk(self.export_state(), storage_path)

    def reset_state(self, storage_path: str = "spatial_memory_state.json") -> None:
        self._tick = 0
        self._odometry.reset()
        self._landmark_tracker.clear()
        self._stimulus_grid.clear()
        try:
            Path(storage_path).unlink(missing_ok=True)
        except OSError:
            pass

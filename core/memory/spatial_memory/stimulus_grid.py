from __future__ import annotations
import math
from typing import Dict, Tuple, Optional
from core.vector import Vector2
from infra.data_models import SensorPacket
from .models import GridCell


class StimulusGrid:
    """Manages the spatial representation of hazards and food incentives."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.grid: Dict[Tuple[int, int], GridCell] = {}

    def record(self, sensors: SensorPacket, pos: Vector2, tick: int) -> None:
        hazard, food = sensors.hazard_stim, sensors.food_stim
        if hazard < self.cfg.stim_threshold and food < self.cfg.stim_threshold:
            return

        key = self.world_to_cell(pos)
        cell = self.grid.setdefault(key, GridCell())
        cell.last_updated_tick = tick

        if hazard >= self.cfg.stim_threshold:
            cell.hazard = min(1.0, cell.hazard + hazard * (1.0 - cell.hazard))
        if food >= self.cfg.stim_threshold:
            cell.food = min(1.0, cell.food + food * (1.0 - cell.food))

    def decay(self) -> None:
        if self.cfg.grid_decay >= 1.0:
            return

        dead = []
        for key, cell in self.grid.items():
            cell.hazard *= self.cfg.grid_decay
            cell.food *= self.cfg.grid_decay
            if (
                cell.hazard < self.cfg.grid_prune_threshold
                and cell.food < self.cfg.grid_prune_threshold
            ):
                dead.append(key)

        for key in dead:
            del self.grid[key]

    def compute_bias(self, position: Vector2, radius: float) -> Vector2:
        bias = Vector2()
        cell_radius = int(math.ceil(radius / self.cfg.cell_size)) + 1
        cx, cy = self.world_to_cell(position)

        for dx in range(-cell_radius, cell_radius + 1):
            for dy in range(-cell_radius, cell_radius + 1):
                key = (cx + dx, cy + dy)
                cell = self.grid.get(key)
                if cell is None:
                    continue

                centre = self.cell_to_world(cx + dx, cy + dy)
                diff = centre - position
                dist_sq = diff.length_sq()

                if dist_sq < 1e-6 or dist_sq > radius * radius:
                    continue

                unit_scaled = diff / dist_sq
                if cell.hazard > 0.0:
                    bias -= unit_scaled * cell.hazard
                if cell.food > 0.0:
                    bias += unit_scaled * cell.food

        return bias

    def world_to_cell(self, pos: Vector2) -> Tuple[int, int]:
        return (
            int(math.floor(pos.x / self.cfg.cell_size)),
            int(math.floor(pos.y / self.cfg.cell_size)),
        )

    def cell_to_world(self, cx: int, cy: int) -> Vector2:
        return Vector2((cx + 0.5) * self.cfg.cell_size, (cy + 0.5) * self.cfg.cell_size)

    def clear(self):
        self.grid.clear()

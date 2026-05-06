"""
Project BIOS — SpatialMemory (Hippocampus)
==========================================
Dead-reckoning odometry + landmark re-zeroing + sparse trauma/bounty grid +
planning bias vector.  No GPS; all coordinates are in the agent's own
internal frame (origin = spawn point).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Tiny Vector2 — avoids numpy dependency while keeping math cleanor
# ---------------------------------------------------------------------------


class Vector2:
    """Lightweight 2-D vector with the operations we actually need."""

    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.x = x
        self.y = y

    # --- arithmetic ----------------------------------------------------------

    def __add__(self, o: "Vector2") -> "Vector2":
        return Vector2(self.x + o.x, self.y + o.y)

    def __sub__(self, o: "Vector2") -> "Vector2":
        return Vector2(self.x - o.x, self.y - o.y)

    def __mul__(self, scalar: float) -> "Vector2":
        return Vector2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> "Vector2":
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> "Vector2":
        return Vector2(self.x / scalar, self.y / scalar)

    def __repr__(self) -> str:
        return f"Vector2({self.x:.3f}, {self.y:.3f})"

    # --- geometry ------------------------------------------------------------

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def length_sq(self) -> float:
        return self.x * self.x + self.y * self.y

    def normalized(self) -> "Vector2":
        mag = self.length()
        return Vector2(self.x / mag, self.y / mag) if mag > 1e-9 else Vector2()

    def dot(self, o: "Vector2") -> float:
        return self.x * o.x + self.y * o.y

    def slide(self, normal: "Vector2") -> "Vector2":
        """Remove the component of *self* that points into *normal*."""
        # v_slide = v - (v · n̂) * n̂ , (only when v · n̂ < 0, i.e. into surface)
        dot = self.dot(normal)
        if dot < 0.0:
            return self - normal * dot
        return Vector2(self.x, self.y)

    def lerp(self, o: "Vector2", t: float) -> "Vector2":
        return self + (o - self) * t

    def copy(self) -> "Vector2":
        return Vector2(self.x, self.y)


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# SpatialMemory
# ---------------------------------------------------------------------------


class SpatialMemory:
    """
    The agent's hippocampus: integrates sensor ticks into a coherent,
    self-correcting internal map.

    Parameters
    ----------
    cell_size : float
        Side length of each trauma/bounty grid cell in world units.
    landmark_alpha : float
        Blending weight for landmark re-zeroing (0 = ignore landmark,
        1 = snap to landmark immediately).  0.15 is a good starting point.
    grid_decay : float
        Per-tick multiplicative decay applied to cell intensities so old
        memories fade.  1.0 = no decay.
    stim_threshold : float
        Minimum hazard_stim / food_stim to record a grid event.
    """

    def __init__(
        self,
        cell_size: float = 50.0,
        landmark_alpha: float = 0.3,
        grid_decay: float = 0.9995,
        stim_threshold: float = 0.1,
    ) -> None:
        # --- odometry state --------------------------------------------------
        self.internal_pos: Vector2 = Vector2(0.0, 0.0)
        self.internal_vel: Vector2 = Vector2(0.0, 0.0)

        # --- landmark map  ---------------------------------------------------
        self._landmarks: Dict[int, LandmarkRecord] = {}

        # --- sparse grid  ----------------------------------------------------
        self._cell_size: float = cell_size
        self._grid: Dict[Tuple[int, int], GridCell] = {}
        self._grid_decay: float = grid_decay

        # --- tuning knobs  ---------------------------------------------------
        self._landmark_alpha: float = landmark_alpha
        self._stim_threshold: float = stim_threshold

        # --- internal tick counter  ------------------------------------------
        self._tick: int = 0

    # =========================================================================
    # Public API — call once per game tick
    # =========================================================================

    def update(self, sensors: dict) -> None:
        """
        Ingest one tick of sensor data and update all internal state.

        Expected keys in *sensors*:
            delta            : float
            accel            : {'x': float, 'y': float}
            current_rotation : float  (radians, absolute compass heading)
            sensed_objects   : list[{'type': str, 'dist': float,
                                     'angle': float, 'id': int}]
            collision_normals: list[{'x': float, 'y': float}]
            hazard_stim      : float  (0–1)
            food_stim        : float  (0–1)
        """
        self._tick += 1
        delta: float = sensors.get("delta", 0.016)

        # 1. Dead reckoning ---------------------------------------------------
        self._integrate_odometry(sensors, delta)

        # 2. Landmark re-zeroing ----------------------------------------------
        self._process_landmarks(sensors)

        # 3. Stimulus grid recording ------------------------------------------
        self._record_stimuli(sensors)

        # 4. Optional grid decay (cheap: iterates only populated cells) -------
        if self._grid_decay < 1.0:
            self._decay_grid()

    # =========================================================================
    # Planning interface
    # =========================================================================

    def get_spatial_bias(
        self,
        position: Optional[Vector2] = None,
        radius: float = 150.0,
    ) -> Vector2:
        """
        Return a bias vector (repulsion from hazards, attraction to food)
        felt at *position* (defaults to current internal_pos).

        The magnitude is proportional to intensity / distance² so that
        nearby strong memories dominate.

        Parameters
        ----------
        position : Vector2 | None
            Query point; defaults to agent's current internal position.
        radius : float
            Ignore grid cells whose centre is farther than this.

        Returns
        -------
        Vector2
            A non-normalised influence vector the planner can add to its
            desired heading.
        """
        if position is None:
            position = self.internal_pos

        bias = Vector2()

        # Determine which grid cells overlap the query radius
        cell_radius = int(math.ceil(radius / self._cell_size)) + 1
        cx, cy = self._world_to_cell(position)

        for dx in range(-cell_radius, cell_radius + 1):
            for dy in range(-cell_radius, cell_radius + 1):
                key = (cx + dx, cy + dy)
                cell = self._grid.get(key)
                if cell is None:
                    continue

                # Cell centre in world coords
                centre = self._cell_to_world(cx + dx, cy + dy)
                diff = centre - position
                dist_sq = diff.length_sq()

                if dist_sq < 1e-6 or dist_sq > radius * radius:
                    continue

                # Influence falls off as 1/d² — use diff/dist_sq directly
                # so direction and magnitude are baked in one shot
                unit_scaled = diff / dist_sq  # direction / dist

                if cell.hazard > 0.0:
                    # Repulsion: push *away* from hazard cell
                    bias = bias - unit_scaled * cell.hazard

                if cell.food > 0.0:
                    # Attraction: pull *toward* food cell
                    bias = bias + unit_scaled * cell.food

        return bias

    # =========================================================================
    # Read-only accessors
    # =========================================================================

    @property
    def position(self) -> Vector2:
        return self.internal_pos.copy()

    @property
    def velocity(self) -> Vector2:
        return self.internal_vel.copy()

    @property
    def landmarks(self) -> Dict[int, LandmarkRecord]:
        return self._landmarks  # caller should treat as read-only

    def get_cell(self, world_pos: Vector2) -> Optional[GridCell]:
        """Return the grid cell at *world_pos*, or None if never recorded."""
        return self._grid.get(self._world_to_cell(world_pos))

    def debug_summary(self) -> str:
        return (
            f"[tick={self._tick}] pos={self.internal_pos} "
            f"vel={self.internal_vel} "
            f"landmarks={len(self._landmarks)} "
            f"grid_cells={len(self._grid)}"
        )

    # =========================================================================
    # Private helpers
    # =========================================================================

    # --- 1. Odometry ---------------------------------------------------------

    def _integrate_odometry(self, sensors: dict, delta: float) -> None:
        """
        Semi-implicit Euler integration with wall-slide correction.

        We integrate acceleration → velocity, then apply collision slide
        *before* updating position so the mental model never "phases" into
        geometry.
        """
        raw_accel = sensors.get("accel", {"x": 0.0, "y": 0.0})
        accel = Vector2(raw_accel["x"], raw_accel["y"])

        # v += a * dt
        self.internal_vel = self.internal_vel + accel * delta

        # Physics correction: slide velocity along each collision normal
        collision_normals = sensors.get("collision_normals", [])
        if collision_normals:
            for raw_n in collision_normals:
                normal = Vector2(raw_n["x"], raw_n["y"]).normalized()
                if normal.length() > 0.01:  # valid normal
                    self.internal_vel = self.internal_vel.slide(normal)

        # Extra kill residual velocity when hitting walls
        if len(collision_normals) > 0:
            self.internal_vel *= 0.3  # strong damping on collision frame

        self.internal_pos = self.internal_pos + self.internal_vel * delta

    # --- 2. Landmark re-zeroing ----------------------------------------------

    def _process_landmarks(self, sensors: dict) -> None:
        """
        For each sensed object:
          • If new → register its estimated world position.
          • If known → compute implied agent position and alpha-blend
            internal_pos toward it (odometry drift correction).
        """
        rotation: float = sensors.get("current_rotation", 0.0)
        cos_r = math.cos(rotation)
        sin_r = math.sin(rotation)

        for obj in sensors.get("sensed_objects", []):
            obj_id: int = obj["id"]
            dist: float = obj["dist"]
            local_angle: float = obj["angle"]  # relative to agent facing

            # Local offset from agent → object (in world frame)
            world_angle = rotation + local_angle
            dx = dist * math.cos(world_angle)
            dy = dist * math.sin(world_angle)
            offset = Vector2(dx, dy)

            if obj_id not in self._landmarks:
                # First sighting: pin landmark at inferred world position
                estimated_world_pos = self.internal_pos + offset
                self._landmarks[obj_id] = LandmarkRecord(
                    pos=estimated_world_pos,
                    last_seen_tick=self._tick,
                )
            else:
                record = self._landmarks[obj_id]
                record.last_seen_tick = self._tick
                record.observation_count += 1

                # Implied agent position given stored landmark coords
                implied_agent_pos = record.pos - offset

                # Alpha-filter: nudge internal_pos toward implied truth
                # Use a confidence-weighted alpha: more observations → more trust
                # but cap at landmark_alpha to stay conservative
                confidence = min(
                    1.0,
                    record.observation_count / 10.0,  # saturates at 10 obs
                )
                effective_alpha = self._landmark_alpha * confidence

                self.internal_pos = self.internal_pos.lerp(
                    implied_agent_pos, effective_alpha
                )

                # Also update the stored landmark position with the *new*
                # implied location so highly-mobile "landmarks" can track
                stored_update_alpha = 0.05 * confidence
                new_landmark_pos = self.internal_pos + offset
                record.pos = record.pos.lerp(new_landmark_pos, stored_update_alpha)

    # --- 3. Stimulus grid recording ------------------------------------------

    def _record_stimuli(self, sensors: dict) -> None:
        """Mark the current cell with any above-threshold stimuli."""
        hazard: float = sensors.get("hazard_stim", 0.0)
        food: float = sensors.get("food_stim", 0.0)

        if hazard < self._stim_threshold and food < self._stim_threshold:
            return  # nothing to record

        key = self._world_to_cell(self.internal_pos)
        cell = self._grid.get(key)
        if cell is None:
            cell = GridCell()
            self._grid[key] = cell

        cell.last_updated_tick = self._tick

        if hazard >= self._stim_threshold:
            # Exponential moving average so repeated exposure accumulates
            cell.hazard = min(1.0, cell.hazard + hazard * (1.0 - cell.hazard))

        if food >= self._stim_threshold:
            cell.food = min(1.0, cell.food + food * (1.0 - cell.food))

    # --- 4. Grid decay -------------------------------------------------------

    def _decay_grid(self) -> None:
        """
        Apply multiplicative decay to all populated cells and prune those
        that have faded to near-zero.  Runs in O(populated_cells).
        """
        dead: List[Tuple[int, int]] = []
        for key, cell in self._grid.items():
            cell.hazard *= self._grid_decay
            cell.food *= self._grid_decay
            if cell.hazard < 1e-4 and cell.food < 1e-4:
                dead.append(key)
        for key in dead:
            del self._grid[key]

    # --- Coordinate conversion helpers --------------------------------------

    def _world_to_cell(self, pos: Vector2) -> Tuple[int, int]:
        """Map a world-space position to a discrete grid key."""
        return (
            int(math.floor(pos.x / self._cell_size)),
            int(math.floor(pos.y / self._cell_size)),
        )

    def _cell_to_world(self, cx: int, cy: int) -> Vector2:
        """Return the *centre* of grid cell (cx, cy) in world space."""
        return Vector2(
            (cx + 0.5) * self._cell_size,
            (cy + 0.5) * self._cell_size,
        )

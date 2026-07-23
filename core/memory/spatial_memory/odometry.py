from __future__ import annotations
import math
from core.vector import Vector2
from infra.data_models import SensorPacket
from infra.constants import MIN_NORMAL_LENGTH


class OdometryTracker:
    """Handles dead reckoning, velocity integration, and wall collisions."""

    def __init__(self):
        self.pos: Vector2 = Vector2(0.0, 0.0)
        self.vel: Vector2 = Vector2(0.0, 0.0)
        self.heading: float = 0.0

    def integrate(self, sensors: SensorPacket, delta: float) -> None:
        self.heading = math.atan2(
            math.sin(sensors.current_rotation), math.cos(sensors.current_rotation)
        )
        accel = Vector2(sensors.accel.x, sensors.accel.y)
        self.vel += accel * delta

        if sensors.collision_normals:
            for raw_n in sensors.collision_normals:
                normal = Vector2(raw_n.x, raw_n.y).normalized()
                if normal.length() > MIN_NORMAL_LENGTH:
                    self.vel = self.vel.slide(normal)

        self.pos += self.vel * delta

    def reset(self):
        self.pos = Vector2(0.0, 0.0)
        self.vel = Vector2(0.0, 0.0)
        self.heading = 0.0

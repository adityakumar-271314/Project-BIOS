from __future__ import annotations
import math
from typing import Dict
from core.vector import Vector2
from infra.data_models import SensorPacket
from .models import LandmarkRecord


class LandmarkTracker:
    """Handles landmark identification and odometry drift correction."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.landmarks: Dict[int, LandmarkRecord] = {}

    def process(
        self, sensors: SensorPacket, current_pos: Vector2, tick: int
    ) -> Vector2:
        rotation: float = sensors.current_rotation

        for obj in sensors.sensed_objects:
            if obj.type != "landmark":
                continue

            world_angle = rotation + obj.angle
            offset = Vector2(
                obj.dist * math.cos(world_angle), obj.dist * math.sin(world_angle)
            )

            if obj.id not in self.landmarks:
                self.landmarks[obj.id] = LandmarkRecord(
                    pos=current_pos + offset,
                    last_seen_tick=tick,
                )
            else:
                record = self.landmarks[obj.id]
                record.last_seen_tick = tick
                record.observation_count += 1

                implied_agent_pos = record.pos - offset
                confidence = min(
                    1.0, record.observation_count / self.cfg.landmark_confidence_divisor
                )
                effective_alpha = self.cfg.landmark_alpha * confidence

                current_pos = current_pos.lerp(implied_agent_pos, effective_alpha)

                if record.observation_count < self.cfg.landmark_confidence_divisor:
                    stored_alpha = self.cfg.landmark_update_alpha * confidence
                    record.pos = record.pos.lerp(current_pos + offset, stored_alpha)

        return current_pos

    def clear(self):
        self.landmarks.clear()

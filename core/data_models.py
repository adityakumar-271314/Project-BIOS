"""
Data Models for Sensor Input and Motor Output.

Defines:
- SensorPacket: All sensory information sent from Godot to Python
- SensedObject: Individual detected entities (food, hazard, landmark)
- MotorOutput: Agent's actuator commands (thrust, steer)
"""



from dataclasses import dataclass, field, asdict
from typing import List
from .vector import Vector2

# =========================================================
# SENSORY OBJECTS
# =========================================================


@dataclass(slots=True)
class SensedObject:
    id: int
    type: str
    dist: float
    angle: float


# =========================================================
# SENSOR PACKET
# =========================================================


@dataclass(slots=True)
class SensorPacket:
    # Timing
    delta: float = 0.016

    # Motion
    accel: Vector2 = field(default_factory=Vector2)

    # Ray sensors
    ray_c: float = 1.0
    ray_l: float = 1.0
    ray_r: float = 1.0

    # Orientation
    current_rotation: float = 0.0

    # Physics state
    is_stuck: bool = False

    # Stimuli
    hazard_stim: float = 0.0
    food_stim: float = 0.0

    # Debug / telemetry
    real_pos_x: float = 0.0
    real_pos_y: float = 0.0

    # Environment
    collision_normals: List[Vector2] = field(default_factory=list)
    sensed_objects: List[SensedObject] = field(default_factory=list)

    # Connection state
    is_real_data: bool = True

    @classmethod
    def from_world_data(cls, world_data: dict) -> "SensorPacket":

        objects = [
            SensedObject(
                id=int(obj.get("id", -1)),
                type=str(obj.get("type", "unknown")),
                dist=float(obj.get("dist", 0.0)),
                angle=-float(obj.get("angle", 0.0)),
            )
            for obj in world_data.get("sensed_objects", [])
        ]

        normals = [
            Vector2(
                x=-float(n.get("x", 0.0)),
                y=-float(n.get("y", 0.0)),
            )
            for n in world_data.get("collision_normals", [])
        ]

        return cls(
            delta=float(world_data.get("delta", 0.016)),
            accel=Vector2(
                x=float(world_data.get("accel", {}).get("x", 0.0)),
                y=-float(world_data.get("accel", {}).get("y", 0.0)),
            ),
            ray_c=float(world_data.get("ray_c", 1.0)),
            ray_l=float(world_data.get("ray_l", 1.0)),
            ray_r=float(world_data.get("ray_r", 1.0)),
            current_rotation=-float(world_data.get("current_rotation", 0.0)),
            collision_normals=normals,
            sensed_objects=objects,
            hazard_stim=float(world_data.get("hazard_stim", 0.0)),
            food_stim=float(world_data.get("food_stim", 0.0)),
            is_stuck=bool(world_data.get("is_stuck", False)),
            real_pos_x=float(world_data.get("global_x", 0.0)),
            real_pos_y=float(world_data.get("global_y", 0.0)),
        )

    def to_dict(self):

        return {
            "delta": self.delta,
            "accel": self.accel.to_dict(),
            "ray_c": self.ray_c,
            "ray_l": self.ray_l,
            "ray_r": self.ray_r,
            "current_rotation": self.current_rotation,
            "is_stuck": self.is_stuck,
            "hazard_stim": self.hazard_stim,
            "food_stim": self.food_stim,
            "real_pos_x": self.real_pos_x,
            "real_pos_y": self.real_pos_y,
            "collision_normals": [n.to_dict() for n in self.collision_normals],
            "sensed_objects": [
                {
                    "id": o.id,
                    "type": o.type,
                    "dist": o.dist,
                    "angle": o.angle,
                }
                for o in self.sensed_objects
            ],
            "is_real_data": self.is_real_data,
        }


# =========================================================
# MOTOR OUTPUT
# =========================================================


@dataclass(slots=True)
class MotorOutput:
    thrust: float = 0.0
    steer: float = 0.0

    def to_dict(self):
        return asdict(self)

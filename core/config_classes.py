from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass(frozen=True)
class BodyConfig:
    velocity_scale: float
    angular_velocity_scale: float
    motion_cost_thrust_coeff: float
    motion_cost_steer_coeff: float
    existence_decay_k: float
    existence_decay_max_energy: float
    stress_tax_coeff: float
    total_cost_divisor: float
    integrity_regen_rate: float
    energy_regen_threshold: float
    starvation_integrity_loss: float
    reserve_transfer_cap: float
    reserve_integrity_penalty_threshold: float
    reserve_integrity_penalty_coeff: float

@dataclass(frozen=True)
class EmotionConfig:
    fear_increase_rate: float
    fear_decay_rate: float
    hazard_trigger_threshold: float
    stress_lerp_rate: float
    wall_stress_threshold: float

@dataclass(frozen=True)
class BrainConfig:
    food_distance_scale: float
    food_force_multiplier: float
    hazard_force_multiplier: float
    memory_steer_multiplier: float
    memory_steer_threshold: float
    wall_force_multiplier: float
    wall_threshold: float
    wander_threshold: float
    steer_smoothing_current: float
    steer_smoothing_previous: float
    thrust_base: float
    thrust_fear_coeff: float
    thrust_stress_coeff: float
    thrust_min: float
    thrust_max: float
    drift_interval_min: int
    drift_interval_max: int
    drift_angle_min: float
    drift_angle_max: float
    random_seed: int

@dataclass(frozen=True)
class MemoryConfig:
    cell_size: float
    landmark_alpha: float
    grid_decay: float
    grid_prune_threshold: float
    stim_threshold: float
    collision_velocity_damping: float
    landmark_confidence_divisor: float
    landmark_update_alpha: float
    bias_radius: float

@dataclass(frozen=True)
class BridgeConfig:
    host: str
    port: int
    fallback_delta: float
    default_ray_value: float
    debug_mode: bool

@dataclass(frozen=True)
class SimulationConfig:
    body: BodyConfig
    emotions: EmotionConfig
    brain: BrainConfig
    memory: MemoryConfig
    bridge: BridgeConfig
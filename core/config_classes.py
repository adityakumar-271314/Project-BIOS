"""
Configuration Data Classes.

Contains frozen dataclasses that define the complete configuration schema
for Project BIOS. Used by config_loader.py to provide type-safe,
immutable configuration objects to all subsystems.
"""


from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeConfig:
    world_seed: int


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
class WanderProfile:
    persistence: int
    thrust_multiplier: float
    priority: float


@dataclass(frozen=True)
class SeekFoodProfile:
    persistence: int
    thrust_multiplier: float
    food_weight: float
    hazard_weight: float


@dataclass(frozen=True)
class AvoidHazardProfile:
    persistence: int
    thrust_multiplier: float
    hazard_weight: float


@dataclass(frozen=True)
class SkillsConfig:
    wander: WanderProfile
    seek_food: SeekFoodProfile
    avoid_hazard: AvoidHazardProfile
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
    fear_threshold: float
    drive_threshold: float
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
    episodic_cooldown_ticks: int
    episodic_significance_threshold: float
    episodic_min_samples: int
    episodic_damage_threshold: float
    episodic_food_recovery_threshold: float
    episodic_danger_fear_threshold: float
    episodic_starvation_drive_threshold: float
    min_std: float
    near_death_integrity: float
    critical_energy: float


@dataclass(frozen=True)
class BridgeConfig:
    host: str
    port: int
    fallback_delta: float
    default_ray_value: float




@dataclass(frozen=True)
class SimulationConfig:
    simulation: RuntimeConfig
    body: BodyConfig
    emotions: EmotionConfig
    brain: BrainConfig
    skills: SkillsConfig
    memory: MemoryConfig
    bridge: BridgeConfig

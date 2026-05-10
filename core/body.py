"""
Module: core.body
Responsibility: Physiological simulation and homeostatic maintenance.
Simulates: 
    - Energy consumption (Metabolic rate + Movement cost).
    - Integrity (Health) loss during starvation or hazard contact.
    - Status signaling (Hunger, Injury) sent to the Emotion Engine.
Dependencies: core.constants, core.data_models
"""


import math
from .constants import MAX_ENERGY, MAX_INTEGRITY


class BodyStateTracker:
    def __init__(self, config):
        self.cfg = config
        self.integrity = MAX_INTEGRITY
        self.energy = MAX_ENERGY
        self.reserves = 0.0
        self.is_alive = True
        self.velocity = 0.0
        self.angular_velocity = 0.0
        self.absolute_rotation = 0.0  # Facing East (0 radians)

    def update(
        self,
        external_damage,
        food_stim,
        stress,
        thrust,
        steer,
        delta,
    ):
        if not self.is_alive:
            return

        self.velocity = thrust * self.cfg.velocity_scale
        self.angular_velocity = steer * self.cfg.angular_velocity_scale

        motion_cost = (abs(thrust) * self.cfg.motion_cost_thrust_coeff) + (
            abs(steer) * self.cfg.motion_cost_steer_coeff
        )
        existence_decay = (math.exp(self.cfg.existence_decay_k * self.energy) - 1) / (
            math.exp(self.cfg.existence_decay_k * MAX_ENERGY) - 1
        )
        stress_tax = stress * self.cfg.stress_tax_coeff

        total_cost = (
            motion_cost + existence_decay + (stress_tax)
        ) / self.cfg.total_cost_divisor
        self.energy = max(0, self.energy - total_cost)

        self.absolute_rotation += self.angular_velocity * delta
        # Keep it in -PI to PI range
        self.absolute_rotation = math.atan2(
            math.sin(self.absolute_rotation), math.cos(self.absolute_rotation)
        )

        if external_damage > 0:
            self.integrity -= external_damage

        if (
            self.energy > self.cfg.energy_regen_threshold
            and external_damage <= 0
            and self.integrity < MAX_INTEGRITY
        ):
            self.integrity = min(
                MAX_INTEGRITY, self.integrity + self.cfg.integrity_regen_rate
            )

        if self.energy <= 0:
            self.integrity -= self.cfg.starvation_integrity_loss

        self.reserves += food_stim
        if self.energy < MAX_ENERGY and self.reserves > 0:
            transfer = min(MAX_ENERGY - self.energy, self.reserves)
            self.energy += transfer
            self.reserves -= transfer

        if self.reserves > self.cfg.reserve_integrity_penalty_threshold:
            self.integrity -= (
                self.reserves - self.cfg.reserve_integrity_penalty_threshold
            ) * self.cfg.reserve_integrity_penalty_coeff

        if self.integrity <= 0:
            self.is_alive = False

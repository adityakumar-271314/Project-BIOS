"""
BaseSkill — Shared Locomotion Logic.

Contains common steering force calculations (walls, drift, smoothing,
thrust modulation) inherited by all concrete skills.
"""
import random
import math
from core.vector import Vector2
from ...data_models import MotorOutput


class BaseSkill:
    
    def __init__(self, brain_cfg, skill_cfg):

        self.cfg = brain_cfg
        self.skill_cfg = skill_cfg
        self.drift_angle = 0.0
        self.drift_timer = 0
        self.last_steer = 0.0
        self.rng = random.Random(self.cfg.random_seed)

    def _wall_force(self, sensor_data):
        wall_force = 0.0

        rl = sensor_data.ray_l
        rr = sensor_data.ray_r

        if rl < self.cfg.wall_threshold:
            wall_force += (
                self.cfg.wall_threshold - rl
            ) * self.cfg.wall_force_multiplier

        if rr < self.cfg.wall_threshold:
            wall_force -= (
                self.cfg.wall_threshold - rr
            ) * self.cfg.wall_force_multiplier

        return wall_force

    def _food_force(self, ehe, sensor_data, multiplier=1.0):
        total = 0.0

        for obj in sensor_data.sensed_objects:
            if obj.type == "food":
                dist_mult = (
                    self.cfg.food_distance_scale
                    / max(obj.dist, 10)
                )

                total -= obj.angle * (
                    ehe.drive
                    * dist_mult
                    * self.cfg.food_force_multiplier
                    * multiplier
                )

        return total

    def _hazard_force(self, ehe, sensor_data, multiplier=1.0):
        total = 0.0

        for obj in sensor_data.sensed_objects:
            if obj.type == "hazard":
                total += obj.angle * (
                    ehe.fear
                    * self.cfg.hazard_force_multiplier
                    * multiplier
                )

        return total

    def _drift_logic(self):
        self.drift_timer -= 1

        if self.drift_timer <= 0:
            self.drift_timer = self.rng.randint(
                self.cfg.drift_interval_min,
                self.cfg.drift_interval_max,
            )

            self.drift_angle = self.rng.uniform(
                -self.cfg.drift_angle_max,
                self.cfg.drift_angle_max,
            )

        return self.drift_angle

    def _smooth_steering(self, steer):
        final_steer = (
            steer * self.cfg.steer_smoothing_current
        ) + (
            self.last_steer
            * self.cfg.steer_smoothing_previous
        )

        self.last_steer = final_steer

        return final_steer

    def _calculate_thrust(self, ehe, multiplier=1.0):
        thrust = (
            self.cfg.thrust_base
            + (ehe.fear * self.cfg.thrust_fear_coeff)
            - (ehe.stress * self.cfg.thrust_stress_coeff)
        )

        thrust *= multiplier

        return self._clamp(
            thrust,
            self.cfg.thrust_min,
            self.cfg.thrust_max,
        )

    def _motor_output(self, steer, thrust):
        return MotorOutput(
            thrust=thrust,
            steer=steer,
        )

    def _clamp(self, value, min_val, max_val):
        return max(min_val, min(value, max_val))
    
    def execute(
                self,
                goal,
                ehe,
                sensor_data,
                spatial_bias,
                memory_system,
                gsm=None
            ):
        raise NotImplementedError
    
    def calculate_heading_steer(
                                self,
                                agent_pos,
                                current_heading,
                                target_pos,
                            ):
        target_dir = target_pos - agent_pos

        target_angle = math.atan2(
            target_dir.y,
            target_dir.x,
        )

        steer_angle = (
            target_angle
            - current_heading
        )

        return math.atan2(
            math.sin(steer_angle),
            math.cos(steer_angle),
        )
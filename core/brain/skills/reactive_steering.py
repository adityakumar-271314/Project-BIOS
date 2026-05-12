import random

from ...data_models import MotorOutput


class ReactiveSteeringSkill:
    """
    Transitional reactive steering system.

    This preserves the current locomotion behavior while allowing
    the architecture above it to evolve independently.
    """

    def __init__(self, config):
        self.cfg = config

        self.drift_angle = 0.0
        self.drift_timer = 0
        self.last_steer = 0.0

        self.rng = random.Random(self.cfg.random_seed)

    def execute(
        self,
        goal,
        ehe,
        sensor_data,
        spatial_bias,
    ):
        food_force = 0.0
        hazard_force = 0.0
        wall_force = 0.0

        sensed = sensor_data.sensed_objects

        for obj in sensed:
            # FOOD ATTRACTION
            if obj.type == "food":
                dist_mult = self.cfg.food_distance_scale / max(obj.dist, 10)

                food_force -= obj.angle * (
                    ehe.drive
                    * dist_mult
                    * self.cfg.food_force_multiplier
                )

            # HAZARD REPULSION
            if obj.type == "hazard":
                hazard_force += obj.angle * (
                    ehe.fear
                    * self.cfg.hazard_force_multiplier
                )

        # WALL REPULSION
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

        total_steer = food_force + hazard_force + wall_force

        # Goal-sensitive behavior
        if goal.name == "wander":
            if abs(total_steer) < self.cfg.wander_threshold:
                total_steer = self._drift_logic()

        # Anti-shiver smoothing
        final_steer = (
            total_steer * self.cfg.steer_smoothing_current
        ) + (
            self.last_steer * self.cfg.steer_smoothing_previous
        )

        self.last_steer = final_steer

        # THRUST
        thrust = (
            self.cfg.thrust_base
            + (ehe.fear * self.cfg.thrust_fear_coeff)
            - (ehe.stress * self.cfg.thrust_stress_coeff)
        )

        return MotorOutput(
            thrust=self._clamp(
                thrust,
                self.cfg.thrust_min,
                self.cfg.thrust_max,
            ),
            steer=final_steer,
        )

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

    def _clamp(self, value, min_val, max_val):
        return max(min_val, min(value, max_val))
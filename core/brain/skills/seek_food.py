from .base import BaseSkill


class SeekFoodSkill(BaseSkill):

    def execute(
        self,
        goal,
        ehe,
        sensor_data,
        spatial_bias,
    ):
        profile = self.skill_cfg.seek_food

        food_force = self._food_force(
            ehe,
            sensor_data,
            multiplier=profile.food_weight,
        )

        hazard_force = self._hazard_force(
            ehe,
            sensor_data,
            multiplier=profile.hazard_weight,
        )

        wall_force = self._wall_force(sensor_data)

        total_steer = (
            food_force
            + hazard_force
            + wall_force
        )

        final_steer = self._smooth_steering(total_steer)

        thrust = self._calculate_thrust(
            ehe,
            multiplier=profile.thrust_multiplier,
        )

        return self._motor_output(
            steer=final_steer,
            thrust=thrust,
        )
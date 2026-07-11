from .base import BaseSkill


class WanderSkill(BaseSkill):

    def execute(
        self,
        goal,
        ehe,
        sensor_data,
        spatial_bias,
        memory_system,
        gsm=None,  # Optional GSM reference for potential target blacklisting
    ):
        profile = self.skill_cfg.wander
        wall_force = self._wall_force(sensor_data)

        total_steer = wall_force

        if abs(total_steer) < self.cfg.wander_threshold:
            total_steer = self._drift_logic()

        final_steer = self._smooth_steering(total_steer)

        thrust = self._calculate_thrust(
            ehe,
            multiplier=profile.thrust_multiplier,
        )

        return self._motor_output(
            steer=final_steer,
            thrust=thrust,
        )

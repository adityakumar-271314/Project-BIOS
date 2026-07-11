"""
Food Seeking Skill.

Supports two strategies:

1. direct_sensory
   - Reactive steering toward currently visible food.

2. memory_nav
   - Navigate toward a remembered food location using world-space memory.
"""

from .base import BaseSkill
import math


class SeekFoodSkill(BaseSkill):

    def execute(
        self,
        goal,
        ehe,
        sensor_data,
        spatial_bias,
        memory_system,
        gsm=None,
    ):

        profile = self.skill_cfg.seek_food

        # =====================================================
        # STRATEGY A : DIRECT SENSORY REACTION
        # =====================================================

        if goal.strategy == "direct_sensory":

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

            total_steer = food_force + hazard_force + wall_force

            final_steer = self._smooth_steering(total_steer)

            thrust = self._calculate_thrust(
                ehe,
                multiplier=profile.thrust_multiplier,
            )

            return self._motor_output(
                steer=final_steer,
                thrust=thrust,
            )

        # =====================================================
        # STRATEGY B : MEMORY NAVIGATION
        # =====================================================

        elif goal.strategy == "memory_nav":

            if goal.spatial_target is None:
                goal.status = "failed"

                return self._motor_output(
                    steer=0.0,
                    thrust=0.0,
                )

            agent_pos = memory_system.position
            agent_vel = memory_system.velocity
            heading = memory_system.internal_heading
            target_pos = goal.spatial_target.target_vector
            radius = goal.spatial_target.hysteresis_radius or 40.0

            distance = (target_pos - agent_pos).magnitude()

            target_dir = target_pos - agent_pos
            target_angle = math.atan2(
                target_dir.y,
                target_dir.x,
            )

            # -------------------------------------------------
            # Reached remembered location
            # -------------------------------------------------

            if distance <= radius:

                food_visible = any(
                    obj.type == "food" for obj in sensor_data.sensed_objects
                )

                if food_visible:
                    goal.status = "done"

                else:
                    goal.status = "failed"
                    print(f"[SEEK] Target failed: {target_pos}")

                    if gsm is not None:
                        gsm.blacklist_target_coordinate(target_pos)
                        print(f"[SEEK] Goal status now {goal.status}")

                return self._motor_output(
                    steer=0.0,
                    thrust=0.0,
                )

            # -------------------------------------------------
            # Continue navigation
            # -------------------------------------------------

            steer = self.calculate_heading_steer(
                agent_pos,
                heading,
                target_pos,
            )

            steer = -steer / math.pi  # Normalize to [-1, 1]

            steer += self._wall_force(sensor_data)

            steer = self._clamp(
                steer,
                -1.0,
                1.0,
            )
            self.last_steer = steer
            thrust = self._calculate_thrust(
                ehe,
                multiplier=profile.thrust_multiplier,
            )

            return self._motor_output(
                steer=steer,
                thrust=thrust,
            )

        # =====================================================
        # UNKNOWN STRATEGY
        # =====================================================

        goal.status = "failed"

        return self._motor_output(
            steer=0.0,
            thrust=0.0,
        )

import math


class BodyStateTracker:
    def __init__(self):
        self.energy = 100.0
        self.integrity = 100.0
        self.reserves = 0.0
        self.is_alive = True

        self.velocity = 0.0
        self.angular_velocity = 0.0
        self.absolute_rotation = 0.0  # Facing East (0 radians)

    def update(
        self,
        external_damage=0,
        food_stim=0,
        stress=0.0,
        thrust=0.0,
        steer=0.0,
        delta=0.016,
    ):
        if not self.is_alive:
            return

        self.velocity = thrust * 120.0
        self.angular_velocity = steer * 4.0

        motion_cost = (abs(thrust) * 0.06) + (abs(steer) * 0.04)
        existence_decay = (math.exp(0.05 * self.energy) - 1) / (
            math.exp(0.05 * 100) - 1
        )
        stress_tax = stress * 0.05

        total_cost = (motion_cost + existence_decay + stress_tax) / 10.0
        self.energy = max(0, self.energy - total_cost)

        self.absolute_rotation += self.angular_velocity * delta
        # Keep it in -PI to PI range
        self.absolute_rotation = math.atan2(
            math.sin(self.absolute_rotation), math.cos(self.absolute_rotation)
        )

        if external_damage > 0:
            self.integrity -= external_damage

        if self.energy > 50 and external_damage <= 0 and self.integrity < 100.0:
            self.integrity = min(100.0, self.integrity + 0.05)

        if self.energy <= 0:
            self.integrity -= 0.2

        self.reserves += food_stim
        if self.energy < 100 and self.reserves > 0:
            transfer = min(100.0 - self.energy, self.reserves, 5.0)
            self.energy += transfer
            self.reserves -= transfer

        if self.reserves > 50:
            self.integrity -= (self.reserves - 50) * 0.01

        if self.integrity <= 0:
            self.is_alive = False

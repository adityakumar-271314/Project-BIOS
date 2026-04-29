import math

class BodyStateTracker:
    def __init__(self):
        self.energy = 100.0
        self.integrity = 100.0
        self.reserves = 0.0
        self.is_alive = True
        
        self.mass = 1.0
        self.velocity = 0.0
        self.angular_velocity = 0.0

    def update(self, external_damage=0, food=0, stress=0.0, thrust=0.0, steer=0.0):
        if not self.is_alive: return

        self.velocity = thrust * 120.0
        self.angular_velocity = steer * 2.0

        # Effort = Linear movement cost + Rotational cost + Stress tax
        motion_cost = (abs(thrust) * 0.06) + (abs(steer) * 0.04)
        existence_decay = (math.exp(0.05 * self.energy) - 1) / (math.exp(0.05 * 100) - 1)
        stress_tax = stress * 0.05
        
        total_cost = motion_cost + existence_decay + stress_tax
        self.energy = max(0, self.energy - (total_cost) / 10)

        self.reserves += food
        self.integrity -= external_damage

        if self.energy > 50 and external_damage == 0 and self.integrity < 100.0:
            self.integrity = min(100.0, self.integrity + 0.05)

        if self.energy <= 0:
            self.integrity -= 0.5 

        if self.energy < 100 and self.reserves > 0:
            transfer = min(100.0 - self.energy, self.reserves, 5.0)
            self.energy += transfer
            self.reserves -= transfer

        if self.integrity <= 0:
            self.is_alive = False
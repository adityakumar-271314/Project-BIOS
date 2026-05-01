import math
import random

class GoalStackManager:
    def __init__(self):
        self.drift_angle = 0.0
        self.drift_timer = 0
        self.last_steer = 0.0

    def evaluate_priorities(self, bst, ehe, sensor_data):
        food_force = 0.0
        hazard_force = 0.0
        wall_force = 0.0
        
        sensed = sensor_data.get("sensed_objects", [])
        
        for obj in sensed:
            # PULL TOWARD FOOD
            if obj["type"] == "food":
                # Stronger pull when hungry and closer
                dist_mult = 100.0 / max(obj["dist"], 10)
                food_force += obj["angle"] * (ehe.drive * dist_mult * 0.5)
                
            # PUSH AWAY FROM FIRE
            if obj["type"] == "hazard":
                # Massive repulsion scaled by fear
                hazard_force -= obj["angle"] * (ehe.fear * 4.5)

        # WALL REPULSION (The "Cushion")
        rl = sensor_data.get("ray_l", 1.0)
        rr = sensor_data.get("ray_r", 1.0)
        
        if rl < 0.7: wall_force += (0.7 - rl) * 3.0
        if rr < 0.7: wall_force -= (0.7 - rr) * 3.0

        # SUM FORCES
        total_steer = food_force + hazard_force + wall_force
        
        # WANDER if nothing is happening
        if abs(total_steer) < 0.1:
            total_steer = self.drift_logic()

        # SMOOTHING (Anti-shiver)
        final_steer = (total_steer * 0.4) + (self.last_steer * 0.6)
        self.last_steer = final_steer

        # THRUST CALCULATION
        thrust = 0.7 + (ehe.fear * 0.4) - (ehe.stress * 0.3)

        return {
            "thrust": self._clamp(thrust, 0.2, 1.1),
            "steer": final_steer
        }

    def drift_logic(self):
        self.drift_timer -= 1
        if self.drift_timer <= 0:
            self.drift_timer = random.randint(60, 150)
            self.drift_angle = random.uniform(-0.5, 0.5)
        return self.drift_angle

    def _clamp(self, value, min_val, max_val):
        return max(min_val, min(value, max_val))
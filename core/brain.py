import math
import random

class GoalStackManager:
    def __init__(self):
        # Maneuver State
        self.target_heading = 0.0
        self.is_maneuvering = False
        self.locked_dir = 0.0
        self.maneuver_timeout = 0
        
        # Stability & Recovery
        self.stuck_recovery_ticks = 0
        self.grace_period_ticks = 0 
        self.cooldown_ticks = 0 
        self.escape_steer = 0.0 # Dynamic recovery steer
        
        # Curiosity State
        self.drift_angle = 0.0
        self.drift_timer = 0
        
        # Thresholds
        self.COLLISION_THRESHOLD = 0.7 
        self.EXIT_THRESHOLD = 0.95
        self.DANGER_ZONE = 0.45

    def evaluate_priorities(self, bst, ehe, sensor_data):
        current_rot = sensor_data.get("current_rotation", 0.0)
        rc = sensor_data.get("ray_c", 1.0)
        rl = sensor_data.get("ray_l", 1.0)
        rr = sensor_data.get("ray_r", 1.0)
        is_stuck = sensor_data.get("is_stuck", False)
        
        min_ray = min(rc, rl, rr)

        if is_stuck or self.stuck_recovery_ticks > 0:
            if self.stuck_recovery_ticks <= 0:
                print("CRITICAL STUCK: Initializing Dynamic Escape")
                self.stuck_recovery_ticks = 70
                self.is_maneuvering = False
                self.escape_steer = random.uniform(0.2, 0.7) 
                self.target_heading = current_rot + math.pi + random.uniform(-0.5, 0.5)
            
            self.stuck_recovery_ticks -= 1
            self.grace_period_ticks = 80 
            
            return {"thrust": -1.0, "steer": self.escape_steer} 

        if self.is_maneuvering:
            self.maneuver_timeout += 1
            angle_error = (self.target_heading - current_rot + math.pi) % (2 * math.pi) - math.pi
            
            if abs(angle_error) < 0.1 and rc > self.EXIT_THRESHOLD:
                self.is_maneuvering = False
                self.maneuver_timeout = 0
                self.grace_period_ticks = 50 
                self.cooldown_ticks = 30
            else:
                if min_ray < self.DANGER_ZONE:
                    self.target_heading += self.locked_dir * 0.08
                return {"thrust": 0.35, "steer": math.tanh(angle_error * 3.0)}

        if self.cooldown_ticks > 0:
            self.cooldown_ticks -= 1
            return {"thrust": 0.9, "steer": 0.0}

        if min_ray < self.COLLISION_THRESHOLD or self.maneuver_timeout > 140:
            self.is_maneuvering = True
            self.maneuver_timeout = 0
            self.locked_dir = 1.0 if rl > rr else -1.0
            
            # This prevents the "Billiard Ball" reflection loop
            turn_mag = random.uniform(1.6, 2.4)
            self.target_heading = current_rot + (self.locked_dir * turn_mag)
            
            return {"thrust": 0.2, "steer": self.locked_dir}

        if self.grace_period_ticks > 0:
            self.grace_period_ticks -= 1
            return {"thrust": 1.0, "steer": 0.0}

        self.drift_timer -= 1
        if self.drift_timer <= 0:
            self.drift_timer = random.randint(80, 160)
            self.drift_angle = random.uniform(-0.2, 0.2) 

        return {"thrust": 0.8, "steer": self.drift_angle}
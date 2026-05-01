class EmotionHormoneEngine:
    def __init__(self):
        self.stress = 0.0
        self.fear = 0.0
        self.drive = 0.0

    def update(self, bst, sensor_data):
        # 1. DRIVE: Normalized hunger
        self.drive = (100.0 - bst.energy) / 100.0
        
        # 2. FEAR: FIXED - hazard_stim is now just the float value
        hazard_stim = sensor_data.get("hazard", 0.0) 
        if hazard_stim > 0.1:
            self.fear = min(1.0, self.fear + 0.3)
        else:
            self.fear = max(0.0, self.fear - 0.02)
            
        # 3. STRESS: Walls + Pain
        integrity_stress = (100.0 - bst.integrity) / 100.0
        rc = sensor_data.get("ray_c", 1.0)
        wall_pressure = (1.0 - rc) if rc < 0.6 else 0.0
        
        target_stress = max(integrity_stress, wall_pressure)
        self.stress += (target_stress - self.stress) * 0.05
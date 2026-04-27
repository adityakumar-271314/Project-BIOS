class EmotionHormoneEngine:
    def __init__(self):
        self.stress = 0.0
        self.fear = 0.0

    def update(self, bst, env_hazards):
        # Stress tracks low integrity
        target_stress = (100 - bst.integrity) / 100.0
        self.stress += (target_stress - self.stress) * 0.1
        
        # Fear spikes with hazard, decays slowly
        if env_hazards > 0:
            self.fear = min(1.0, self.fear + 0.4)
        else:
            self.fear = max(0.0, self.fear - 0.02)
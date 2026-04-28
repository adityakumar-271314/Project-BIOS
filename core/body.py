import math

class BodyStateTracker:
    def __init__(self):
        self.energy = 100.0
        self.integrity = 100.0
        self.reserves = 0.0
        self.is_alive = True

    def update(self, external_damage=0, food=0):
        if not self.is_alive: return
        
        # Metabolic Decay: Higher energy = higher burn rate
        decay_rate = (math.exp(0.05 * self.energy) - 1) / (math.exp(0.05 * 100) - 1)
        self.energy = max(0, self.energy - decay_rate)
        self.reserves += food 
        
        self.integrity -= external_damage


        if self.energy > 50 and external_damage == 0 and self.integrity < 100.0:
            self.integrity = min(100.0, self.integrity + 0.05)

       
        if self.energy <= 0:
            self.integrity -= 0.5 

        if self.energy < 100 and self.reserves > 0:
            transfer_amount = min(100.0 - self.energy, self.reserves, 5.0)
            self.energy += transfer_amount
            self.reserves -= transfer_amount

        # Overeating Penalty
        if self.reserves > 50:
            self.integrity -= 0.1 * (self.reserves / 50)
        
        if self.integrity <= 0:
            self.is_alive = False
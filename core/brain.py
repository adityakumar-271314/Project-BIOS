import math

class GoalStackManager:
    def __init__(self):
        self.current_goal = "WANDER"
        self.persistence = 1.1 

    def _sigmoidal_curve(self, value, threshold=40, steepness=-0.15):
        return 100 / (1 + math.exp(-steepness * (value - threshold)))

    def evaluate_priorities(self, bst, ehe):
        hunger_drive = self._sigmoidal_curve(bst.energy, threshold=30)
        safety_drive = ehe.fear * 120 
        recuperation_drive = (100 - bst.integrity) + (ehe.stress * 50)
        curiosity_drive = 10.0 

        scores = {
            "FORAGE": hunger_drive,
            "HIDE": safety_drive,
            "REST": recuperation_drive,
            "WANDER": curiosity_drive
        }

        if self.current_goal in scores:
            scores[self.current_goal] *= self.persistence

        self.current_goal = max(scores, key=scores.get)
        return self.current_goal, scores
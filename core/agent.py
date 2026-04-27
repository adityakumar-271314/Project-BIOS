from .body import BodyStateTracker
from .emotions import EmotionHormoneEngine
from .brain import GoalStackManager

class Agent:
    def __init__(self):
        self.bst = BodyStateTracker()
        self.ehe = EmotionHormoneEngine()
        self.gsm = GoalStackManager()
        self.current_action = "WANDER"

    def tick(self, env_damage=0, food=0):
        if not self.bst.is_alive:
            return "DECEASED"
        
        self.bst.update(env_damage, food)
        self.ehe.update(self.bst, env_damage)
        self.current_action, scores = self.gsm.evaluate_priorities(self.bst, self.ehe)

        return self.current_action, scores
from .body import BodyStateTracker
from .emotions import EmotionHormoneEngine
from .brain import GoalStackManager

class Agent:
    def __init__(self):
        self.bst = BodyStateTracker()
        self.ehe = EmotionHormoneEngine()
        self.bst_manager = GoalStackManager()

    def tick(self, env_damage, food, sensor_data):
        
        self.ehe.update(self.bst, sensor_data)

        self.bst.update(
            external_damage=env_damage,
            food_stimulus=food,
            stress=self.ehe.stress
        )

        motor_output = self.bst_manager.evaluate_priorities(
            self.bst, 
            self.ehe, 
            sensor_data
        )

        self.bst.update(
            thrust=motor_output.get("thrust", 0.0),
            steer=motor_output.get("steer", 0.0)
        )

        return motor_output
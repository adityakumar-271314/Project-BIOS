from .body import BodyStateTracker
from .emotions import EmotionHormoneEngine
from .brain import GoalStackManager

class Agent:
    def __init__(self):
        self.bst = BodyStateTracker()
        self.ehe = EmotionHormoneEngine()
        self.gsm = GoalStackManager()
        self.motor_output = {"thrust": 0.0, "steer": 0.0}

    def tick(self, env_damage=0, food=0, sensor_data=None):
        if sensor_data is None:
            sensor_data = {}

        if not self.bst.is_alive:
            return {"thrust": 0.0, "steer": 0.0, "status": "DECEASED"}
        

        self.bst.update(
            external_damage=env_damage, 
            food=food, 
            stress=self.ehe.stress,
            thrust=self.motor_output.get("thrust", 0.0),
            steer=self.motor_output.get("steer", 0.0)
        )

        self.ehe.update(self.bst, env_damage)
        
        self.motor_output = self.gsm.evaluate_priorities(self.bst, self.ehe, sensor_data)

        return self.motor_output
from .body import BodyStateTracker
from .emotions import EmotionHormoneEngine
from .brain import GoalStackManager
from .hippocampus import SpatialMemory, Vector2


class Agent:
    def __init__(self):
        self.bst = BodyStateTracker()
        self.ehe = EmotionHormoneEngine()
        self.gsm = GoalStackManager()
        self.memory = SpatialMemory(cell_size=50.0, landmark_alpha=0.2)

    def tick(self, env_damage, food, sensor_data, delta=0.016):

        self.memory.update(sensor_data)
        spatial_bias = self.memory.get_spatial_bias()
        self.ehe.update(self.bst, sensor_data)
        motor_output = self.gsm.evaluate_priorities(self.ehe, sensor_data, spatial_bias)

        self.bst.update(
            stress=self.ehe.stress,
            external_damage=env_damage,
            food_stim=food,
            thrust=motor_output.get("thrust", 0.0),
            steer=motor_output.get("steer", 0.0),
            delta=delta,
        )

        return motor_output

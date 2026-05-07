from .body import BodyStateTracker
from .emotions import EmotionHormoneEngine
from .brain import GoalStackManager
from .hippocampus import SpatialMemory
from .config_loader import load_config

class Agent:
    def __init__(self, config_path="config.json"):

        self.config = load_config(config_path)
        self.bst = BodyStateTracker(self.config.body)
        self.ehe = EmotionHormoneEngine(self.config.emotions)
        self.gsm = GoalStackManager(self.config.brain)
        self.memory = SpatialMemory(self.config.memory)
        self.tick_count = 0

    def tick(self, env_damage, food, sensor_data, delta=None):
        
        self.tick_count += 1
        dt = delta if delta is not None else sensor_data.delta
        self.memory.update(sensor_data)
        spatial_bias = self.memory.get_spatial_bias(radius=self.config.memory.bias_radius)
        motor_output = self.gsm.evaluate_priorities(self.ehe, sensor_data, spatial_bias)
        self.ehe.update(self.bst, sensor_data)
        self.bst.update(
            stress=self.ehe.stress,
            external_damage=env_damage,
            food_stim=food,
            thrust=motor_output.thrust,
            steer=motor_output.steer,
            delta=dt,
        )

        return motor_output

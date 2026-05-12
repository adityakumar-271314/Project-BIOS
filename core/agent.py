"""
Module: core.agent
Responsibility: High-level orchestration of the BIOS entity.
Workflow: 
    1. Receives raw sensor packets from bridge.py.
    2. Routes data to Hippocampus (Memory) and Body (Physiology).
    3. Requests a decision from the Brain (Logic).
    4. Returns actuator commands (Thrust/Steer) back to the bridge.
Dependencies: core.brain, core.hippocampus, core.body, core.telemetry
"""



from logging import config
from .body import BodyStateTracker
from .emotions import EmotionHormoneEngine
from core.brain.brain import Brain
from .hippocampus import SpatialMemory
from .config_loader import load_config


class Agent:
    def __init__(self, config_path="config.json"):

        self.config = load_config(config_path)
        self.bst = BodyStateTracker(self.config.body)
        self.ehe = EmotionHormoneEngine(self.config.emotions)
        self.brain = Brain(
            brain_cfg=self.config.brain,
            skill_cfg=self.config.skills,
        )
        self.memory = SpatialMemory(self.config.memory)
        self.tick_count = 0

    def tick(self, env_damage, food, sensor_data, delta=None):

        self.tick_count += 1
        dt = delta if delta is not None else sensor_data.delta
        self.memory.update(sensor_data)
        self.ehe.update(self.bst, sensor_data)
        spatial_bias = self.memory.get_spatial_bias(
            radius=self.config.memory.bias_radius
        )
        motor_output = self.brain.evaluate_priorities(self.ehe, sensor_data, spatial_bias)
        self.bst.update(
            stress=self.ehe.stress,
            external_damage=env_damage,
            food_stim=food,
            thrust=motor_output.thrust,
            steer=motor_output.steer,
            delta=dt,
        )

        return motor_output

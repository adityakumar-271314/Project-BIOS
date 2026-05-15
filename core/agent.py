"""
Core Agent Orchestrator.

High-level coordinator that binds together the major subsystems of the BIOS agent:

- BodyStateTracker (physiology & energy)
- EmotionHormoneEngine (internal drives)
- SpatialMemory (hippocampus)
- Brain (goal selection + skill execution)

One `tick()` call represents one simulation step. It follows this flow:
1. Update spatial memory with latest sensor data
2. Update emotional/hormonal state
3. Request motor decision from the Brain
4. Update body physiology (energy, integrity, motion cost)
"""


from core.memory.memory_system import MemorySystem

from .body import BodyStateTracker
from .emotions import EmotionHormoneEngine
from core.brain.brain import Brain
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
        self.memory = MemorySystem(self.config.memory)
        self.tick_count = 0

    def tick(self, env_damage, food, sensor_data, delta=None):

        self.tick_count += 1
        dt = delta if delta is not None else sensor_data.delta
        self.memory.update(
            sensors=sensor_data,
            body=self.bst,
            emotions=self.ehe,
        )
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

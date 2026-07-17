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
from core.body import BodyStateTracker
from core.emotions import EmotionHormoneEngine
from core.brain.brain import Brain
from infra.config_loader import load_config
from infra.agent_state import AgentState

class Agent:
    def __init__(self, config_path="config.json"):

        self.config = load_config(config_path)
        self.bst = BodyStateTracker(self.config.body)
        self.ehe = EmotionHormoneEngine(self.config.emotions)
        self.memory = MemorySystem(self.config.memory)
        self.brain = Brain(
            brain_cfg=self.config.brain,
            skill_cfg=self.config.skills,
            memory_system=self.memory,
        )
        self.tick_count = 0

    def tick(self, env_damage, food, sensor_data, delta=None):

        self.tick_count += 1
        dt = delta if delta is not None else sensor_data.delta
        self.ehe.update(self.bst, sensor_data)
        spatial_bias = self.memory.get_spatial_bias(
            radius=self.config.memory.bias_radius
        )
        motor_output = self.brain.evaluate_priorities(
            self.ehe,
            sensor_data,
            spatial_bias,
        )
        current_goal = self.brain.gsm.active_goal
        current_skill = self.brain.adse.active_skill_name
        target_vector = None
        if current_goal and current_goal.spatial_target:
            target_vector = current_goal.spatial_target.target_vector

        self.memory.update(
            sensors=sensor_data,
            body=self.bst,
            emotions=self.ehe,
            active_goal=current_goal,
            active_skill=current_skill,
            target=target_vector,
        )
        self.bst.update(
            stress=self.ehe.stress,
            external_damage=env_damage,
            food_stim=food,
            thrust=motor_output.thrust,
            steer=motor_output.steer,
            delta=dt,
        )

        return motor_output

    def export_state(self) -> AgentState:
        return AgentState.from_agent(self)

    def import_state(self, state: AgentState) -> None:
        self.tick_count = state.tick_count

        self.bst.energy = state.energy
        self.bst.integrity = state.integrity

        self.ehe.stress = state.stress
        self.ehe.fear = state.fear
        self.ehe.drive = state.drive

        self.memory.internal_pos.x = state.internal_pos_x
        self.memory.internal_pos.y = state.internal_pos_y

        self.memory.internal_vel.x = state.internal_vel_x
        self.memory.internal_vel.y = state.internal_vel_y

        self.bst.is_alive = state.is_alive
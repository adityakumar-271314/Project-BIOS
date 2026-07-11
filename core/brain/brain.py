"""
Brain Facade.

Provides a clean high-level interface to the cognitive architecture.
Delegates to:
- GoalStackManager (GSM) for goal selection
- ActionDispatcher (ADSE) for skill execution
"""

from .gsm import GoalStackManager
from .adse import ActionDispatcher


class Brain:

    def __init__(self, brain_cfg, skill_cfg, memory_system):
        self.gsm = GoalStackManager(brain_cfg, skill_cfg, memory_system)

        self.adse = ActionDispatcher(
            brain_cfg,
            skill_cfg,
            memory_system,
        )
        self.memory_system = memory_system

    def evaluate_priorities(self, ehe, sensor_data, spatial_bias):
        """
        Evaluates active goals and routes them to behavior execution.
        Returns the direct motor control dictionary payload to the agent loop.
        """
        memory_system = self.memory_system
        goal = self.gsm.evaluate_goal(
            ehe,
            sensor_data,
        )
        return self.adse.execute(
            goal=goal,
            ehe=ehe,
            sensor_data=sensor_data,
            spatial_bias=spatial_bias,
            memory_system=memory_system,
            gsm=self.gsm,
        )

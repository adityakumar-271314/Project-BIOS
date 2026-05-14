"""
Brain Facade.

Provides a clean high-level interface to the cognitive architecture.
Currently delegates to:
- GoalStackManager (GSM) for goal selection
- ActionDispatcher (ADSE) for skill execution
"""



from .gsm import GoalStackManager
from .adse import ActionDispatcher


class Brain:

    def __init__(self, brain_cfg, skill_cfg):

        self.gsm = GoalStackManager(
            brain_cfg,
            skill_cfg,
        )

        self.adse = ActionDispatcher(
            brain_cfg,
            skill_cfg,
        )
    def evaluate_priorities(self, ehe, sensor_data, spatial_bias):
        goal = self.gsm.evaluate_goal(ehe, sensor_data)

        return self.adse.execute(
            goal=goal,
            ehe=ehe,
            sensor_data=sensor_data,
            spatial_bias=spatial_bias,
        )
from .gsm import GoalStackManager
from .adse import ActionDispatcher


class Brain:
    """
    Transitional facade preserving the old brain interface.

    External systems can continue calling:
        brain.evaluate_priorities(...)

    Internally the architecture is now split into:
        - Goal selection (GSM)
        - Action execution (ADSE)
    """

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
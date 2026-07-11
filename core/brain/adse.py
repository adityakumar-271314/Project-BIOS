"""
Action Dispatcher & Skill Executor (ADSE).

Routes the selected goal to the appropriate Skill implementation and
returns concrete motor commands.
"""

from .skills.wander import WanderSkill
from .skills.seek_food import SeekFoodSkill
from .skills.avoid_hazard import AvoidHazardSkill


class ActionDispatcher:

    def __init__(self, brain_cfg, skill_cfg, memory_system):

        self.cfg = brain_cfg
        self.skill_cfg = skill_cfg
        self.memory_system = memory_system
        self.active_skill_name = "wander"

        self.skills = {
            "wander": WanderSkill(
                brain_cfg,
                skill_cfg,
            ),
            "seek_food": SeekFoodSkill(
                brain_cfg,
                skill_cfg,
            ),
            "avoid_hazard": AvoidHazardSkill(
                brain_cfg,
                skill_cfg,
            ),
        }

    def execute(
        self,
        goal,
        ehe,
        sensor_data,
        spatial_bias,
        memory_system,
        gsm=None,  # Optional GSM reference for skills that may need to blacklist targets
    ):
        skill = self.skills.get(goal.name)
        if skill is None:
            skill = self.skills["wander"]
        self.active_skill_name = goal.name if goal.name in self.skills else "wander"

        return skill.execute(
            goal=goal,
            ehe=ehe,
            sensor_data=sensor_data,
            spatial_bias=spatial_bias,
            memory_system=memory_system,
            gsm=gsm,
        )

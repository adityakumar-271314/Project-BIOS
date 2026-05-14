"""
Action Dispatcher & Skill Executor (ADSE).

Routes the selected goal to the appropriate Skill implementation and
returns concrete motor commands.
"""



from .skills.wander import WanderSkill
from .skills.seek_food import SeekFoodSkill
from .skills.avoid_hazard import AvoidHazardSkill


class ActionDispatcher:
    
    def __init__(self, brain_cfg, skill_cfg):

        self.cfg = brain_cfg
        self.skill_cfg = skill_cfg

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
    ):
        skill = self.skills.get(goal.name)

        if skill is None:
            skill = self.skills["wander"]

        return skill.execute(
            goal=goal,
            ehe=ehe,
            sensor_data=sensor_data,
            spatial_bias=spatial_bias,
        )
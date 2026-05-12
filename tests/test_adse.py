from core.brain.adse import ActionDispatcher
from core.brain.skills.wander import WanderSkill
from core.brain.skills.seek_food import SeekFoodSkill
from core.brain.skills.avoid_hazard import AvoidHazardSkill

from core.config_loader import load_config


def test_goal_dispatches_correct_skill():
    cfg = load_config()

    adse = ActionDispatcher(
        cfg.brain,
        cfg.skills,
    )

    assert isinstance(
        adse.skills["wander"],
        WanderSkill,
    )

    assert isinstance(
        adse.skills["seek_food"],
        SeekFoodSkill,
    )

    assert isinstance(
        adse.skills["avoid_hazard"],
        AvoidHazardSkill,
    )
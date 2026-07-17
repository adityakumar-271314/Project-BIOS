from core.brain.adse import ActionDispatcher
from core.brain.skills.wander import WanderSkill
from core.brain.skills.seek_food import SeekFoodSkill
from core.brain.skills.avoid_hazard import AvoidHazardSkill
from core.memory.memory_system import MemorySystem
from infra.config_loader import load_config


def test_goal_dispatches_correct_skill():
    cfg = load_config()
    memory_system = MemorySystem
    adse = ActionDispatcher(
        cfg.brain,
        cfg.skills,
        memory_system,
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

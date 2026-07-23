from core.brain.gsm import GoalStackManager
from infra.config_loader import load_config
from infra.data_models import SensorPacket, SensedObject
from core.brain.gsm import Goal
from core.memory.memory_system import MemorySystem


class DummyEmotion:
    def __init__(self):
        self.drive = 0.0
        self.fear = 0.0
        self.stress = 0.0


def build_gsm():
    cfg = load_config()
    memory_system = MemorySystem(cfg.memory)
    return GoalStackManager(cfg.brain, cfg.skills, memory_system=memory_system)


def test_goal_persistence():
    gsm = build_gsm()

    emotions = DummyEmotion()
    emotions.drive = 1.0

    sensors = SensorPacket(
        sensed_objects=[
            SensedObject(
                id=1,
                type="food",
                dist=30,
                angle=0.2,
            )
        ]
    )

    first_goal: Goal = gsm.evaluate_goal(
        emotions,
        sensors,
    )

    second_goal: Goal = gsm.evaluate_goal(
        emotions,
        sensors,
    )

    assert first_goal.name == second_goal.name
    assert gsm.goal_age > 0


def test_hazard_interrupts_food_goal():
    gsm = build_gsm()

    emotions = DummyEmotion()
    emotions.drive = 1.0

    food_packet = SensorPacket(
        sensed_objects=[
            SensedObject(
                id=1,
                type="food",
                dist=30,
                angle=0.2,
            )
        ]
    )

    goal: Goal = gsm.evaluate_goal(
        emotions,
        food_packet,
    )

    assert goal.name == "seek_food"

    emotions.fear = 1.0

    hazard_packet = SensorPacket(
        sensed_objects=[
            SensedObject(
                id=2,
                type="hazard",
                dist=10,
                angle=-0.5,
            )
        ]
    )

    goal: Goal = gsm.evaluate_goal(
        emotions,
        hazard_packet,
    )

    assert goal.name == "avoid_hazard"

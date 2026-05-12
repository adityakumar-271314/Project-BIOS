from core.brain.brain import Brain
from core.config_loader import load_config
from core.data_models import SensorPacket, SensedObject
from core.vector import Vector2


class DummyEmotion:
    def __init__(self):
        self.drive = 1.0
        self.fear = 0.0
        self.stress = 0.0


def test_food_creates_steering_force():
    cfg = load_config()

    brain = Brain(
        brain_cfg=cfg.brain,
        skill_cfg=cfg.skills,
    )

    sensors = SensorPacket(
        sensed_objects=[
            SensedObject(
                id=1,
                type="food",
                dist=50,
                angle=0.5,
            )
        ]
    )

    output = brain.evaluate_priorities(
        DummyEmotion(),
        sensors,
        Vector2(),
    )

    assert output.steer != 0


def test_thrust_is_clamped():
    cfg = load_config()

    brain = Brain(
        brain_cfg=cfg.brain,
        skill_cfg=cfg.skills,
    )

    emotions = DummyEmotion()
    emotions.fear = 100

    sensors = SensorPacket()

    output = brain.evaluate_priorities(
        emotions,
        sensors,
        Vector2(),
    )

    assert output.thrust <= brain.adse.cfg.thrust_max
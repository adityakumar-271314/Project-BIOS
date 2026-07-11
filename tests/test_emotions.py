from core.emotions import EmotionHormoneEngine
from core.config_loader import load_config
from core.body import BodyStateTracker
from core.data_models import SensorPacket


def test_fear_increases_with_hazard():
    cfg = load_config().emotions

    ehe = EmotionHormoneEngine(cfg)

    bst = BodyStateTracker(load_config().body)

    sensors = SensorPacket(hazard_stim=1.0)

    ehe.update(bst, sensors)

    assert ehe.fear > 0


def test_fear_decays_without_hazard():
    cfg = load_config().emotions

    ehe = EmotionHormoneEngine(cfg)

    ehe.fear = 1.0

    bst = BodyStateTracker(load_config().body)

    sensors = SensorPacket(hazard_stim=0.0)

    ehe.update(bst, sensors)

    assert ehe.fear < 1.0


def test_drive_increases_when_energy_low():
    cfg = load_config().emotions

    ehe = EmotionHormoneEngine(cfg)

    bst = BodyStateTracker(load_config().body)

    bst.energy = 20

    sensors = SensorPacket()

    ehe.update(bst, sensors)

    assert ehe.drive > 0.5

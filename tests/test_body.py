from core.body import BodyStateTracker
from infra.config_loader import load_config


def test_energy_decreases_after_update():
    cfg = load_config().body
    body = BodyStateTracker(cfg)

    start_energy = body.energy

    body.update(
        external_damage=0,
        food_stim=0,
        stress=0.5,
        thrust=1.0,
        steer=0.5,
        delta=0.016,
    )

    assert body.energy < start_energy


def test_integrity_decreases_from_damage():
    cfg = load_config().body
    body = BodyStateTracker(cfg)

    body.update(
        external_damage=10,
        food_stim=0,
        stress=0,
        thrust=0,
        steer=0,
        delta=0.016,
    )

    assert body.integrity == 90


def test_agent_dies_when_integrity_zero():
    cfg = load_config().body
    body = BodyStateTracker(cfg)

    body.integrity = 1

    body.update(
        external_damage=5,
        food_stim=0,
        stress=0,
        thrust=0,
        steer=0,
        delta=0.016,
    )

    assert body.is_alive is False


def test_food_restores_energy():
    cfg = load_config().body
    body = BodyStateTracker(cfg)

    body.energy = 50

    body.update(
        external_damage=0,
        food_stim=20,
        stress=0,
        thrust=0,
        steer=0,
        delta=0.016,
    )

    assert body.energy > 50

from core.config_loader import load_config


def test_config_loads():
    cfg = load_config()

    assert cfg.body.velocity_scale > 0
    assert cfg.brain.thrust_base > 0


def test_world_seed_exists():
    cfg = load_config()

    assert cfg.simulation.world_seed == 999
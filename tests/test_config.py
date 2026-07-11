from core.config_loader import load_config


def test_config_loads():
    cfg = load_config()

    assert cfg.body.velocity_scale > 0
    assert cfg.brain.thrust_base > 0


def test_world_seed_exists():
    cfg = load_config()

    assert isinstance(cfg.simulation.world_seed, int)


def test_skill_profile_loads_correctly():
    cfg = load_config()

    assert cfg.skills.seek_food.food_weight == 1.40

    assert cfg.skills.avoid_hazard.hazard_weight == 2.20

    assert cfg.skills.wander.persistence == 45

import pytest
from core.memory.memory_system import MemorySystem
from core.memory.semantic import SemanticMemory
from core.config_loader import load_config
from core.data_models import SensorPacket
from core.vector import Vector2
from core.memory.schemas import TickSnapshot
from core.memory.episodic import EpisodicMemory
from core.config_loader import load_config


def test_odometry_updates_position():
    mem = SemanticMemory(load_config().memory)

    sensors = SensorPacket(
        accel=Vector2(10, 0),
        delta=1.0,
    )

    mem.update(sensors)

    assert mem.internal_pos.x > 0


def test_hazard_memory_recorded():
    mem = SemanticMemory(load_config().memory)

    sensors = SensorPacket(
        hazard_stim=1.0,
    )

    mem.update(sensors)

    assert len(mem._grid) > 0


def test_landmark_registration():
    from core.data_models import SensedObject

    mem = SemanticMemory(load_config().memory)

    sensors = SensorPacket(
        sensed_objects=[
            SensedObject(
                id=42,
                type="landmark",
                dist=100,
                angle=0,
            )
        ]
    )

    mem.update(sensors)

    assert 42 in mem.landmarks


from core.memory.episodic import RunningStats
import math


def test_running_stats_mean_and_variance():
    stats = RunningStats()

    for value in [1, 2, 3, 4]:
        stats.update(value)

    assert stats.n == 4
    assert stats.mean == 2.5
    assert math.isclose(stats.variance, 1.6666666666)
def test_running_stats_empty():
    stats = RunningStats()

    assert stats.mean == 0.0
    assert stats.variance == 0.0
    assert stats.std == 0.0


def make_snapshot(**kwargs):
    defaults = dict(
        tick=0,
        pos_x=0,
        pos_y=0,
        vel_x=0,
        vel_y=0,
        heading=0,
        energy=100,
        integrity=100,
        stress=0,
        fear=0,
        drive=0,
    )
    defaults.update(kwargs)
    return TickSnapshot(**defaults)


def test_compute_deltas():
    memory = EpisodicMemory(load_config().memory)

    a = make_snapshot(
        energy=100,
        integrity=90,
        stress=0.2,
        fear=0.3,
        drive=0.4,
    )

    b = make_snapshot(
        energy=90,
        integrity=80,
        stress=0.5,
        fear=0.1,
        drive=0.9,
    )

    d = memory.compute_deltas(a, b)

    assert d["energy_delta"] == -10
    assert d["integrity_delta"] == -10
    assert d["stress_delta"] == pytest.approx(0.3)
    assert d["fear_delta"] == pytest.approx(-0.2)
    assert d["drive_delta"] == pytest.approx(0.5)


def test_damage_spike_category():
    mem = EpisodicMemory(load_config().memory)

    snap = make_snapshot()

    deltas = {
        "energy_delta":0,
        "integrity_delta":-999,
        "stress_delta":0,
        "fear_delta":0,
        "drive_delta":0,
    }

    assert mem.categorize_event(deltas, snap) == "damage_spike"


def test_food_recovery_category():
    mem = EpisodicMemory(load_config().memory)

    snap = make_snapshot()

    deltas = {
        "energy_delta":999,
        "integrity_delta":0,
        "stress_delta":0,
        "fear_delta":0,
        "drive_delta":0,
    }

    assert mem.categorize_event(deltas, snap) == "food_recovery"


def test_hazard_category():
    mem = EpisodicMemory(load_config().memory)

    snap = make_snapshot(hazard_stim=1.0)

    deltas = {
        "energy_delta":0,
        "integrity_delta":0,
        "stress_delta":0,
        "fear_delta":0,
        "drive_delta":0,
    }

    assert mem.categorize_event(deltas, snap) == "hazard_encounter"


def test_surprise_zero_before_minimum_samples():
    mem = EpisodicMemory(load_config().memory)

    assert mem.compute_surprise("energy_delta", 100) == 0


def test_surprise_positive_after_training():
    mem = EpisodicMemory(load_config().memory)

    cfg = mem.cfg

    for _ in range(cfg.episodic_min_samples):
        mem._stats["energy_delta"].update(0)

    surprise = mem.compute_surprise("energy_delta", 20)

    assert surprise > 0


def test_semantic_memory_export_import():

    cfg = load_config().memory

    semantic = SemanticMemory(cfg)

    semantic.internal_pos = Vector2(10.0, 20.0)
    semantic.internal_vel = Vector2(1.0, -2.0)

    exported = semantic.export_state()

    restored = SemanticMemory(cfg)
    restored.import_state(exported)

    assert restored.internal_pos.x == 10.0
    assert restored.internal_pos.y == 20.0

    assert restored.internal_vel.x == 1.0
    assert restored.internal_vel.y == -2.0


def test_memory_system_roundtrip():

    cfg = load_config().memory

    memory = MemorySystem(cfg)

    exported = memory.export_state()

    restored = MemorySystem(cfg)
    restored.import_state(exported)

    assert restored.export_state() == exported

from core.memory.memory_system import MemorySystem
from core.memory.semantic import SemanticMemory
from core.config_loader import load_config
from core.data_models import SensorPacket
from core.vector import Vector2
from core.memory.episodic import EpisodicMemory
from core.memory.schemas import EpisodicEvent

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

def test_episodic_event_roundtrip():



    event = EpisodicEvent(
        tick=10,
        event_type="danger_state",
        significance=4.5,
        pos_x=12.0,
        pos_y=-3.0,

        energy=80.0,
        integrity=90.0,

        stress=0.4,
        fear=0.7,
        drive=0.2,

        energy_delta=-2.0,
        integrity_delta=-5.0,

        stress_delta=0.1,
        fear_delta=0.3,
        drive_delta=0.0,
    )

    data = event.to_dict()

    rebuilt = EpisodicEvent.from_dict(data)

    assert rebuilt.tick == event.tick
    assert rebuilt.event_type == event.event_type
    assert rebuilt.pos_x == event.pos_x
    assert rebuilt.integrity_delta == event.integrity_delta

def test_episodic_memory_export_import():




    cfg = load_config().memory

    memory = EpisodicMemory(cfg)

    memory.events.append(
        EpisodicEvent(
            tick=1,
            event_type="test",
            significance=1.0,

            pos_x=1.0,
            pos_y=2.0,

            energy=50.0,
            integrity=100.0,

            stress=0.1,
            fear=0.2,
            drive=0.3,

            energy_delta=-1.0,
            integrity_delta=0.0,

            stress_delta=0.0,
            fear_delta=0.0,
            drive_delta=0.0,
        )
    )

    exported = memory.export_state()

    restored = EpisodicMemory(cfg)
    restored.import_state(exported)

    assert len(restored.events) == 1
    assert restored.events[0].event_type == "test"

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


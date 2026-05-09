from core.hippocampus import SpatialMemory
from core.config_loader import load_config
from core.data_models import SensorPacket
from core.vector import Vector2


def test_odometry_updates_position():
    mem = SpatialMemory(load_config().memory)

    sensors = SensorPacket(
        accel=Vector2(10, 0),
        delta=1.0,
    )

    mem.update(sensors)

    assert mem.internal_pos.x > 0


def test_hazard_memory_recorded():
    mem = SpatialMemory(load_config().memory)

    sensors = SensorPacket(
        hazard_stim=1.0,
    )

    mem.update(sensors)

    assert len(mem._grid) > 0


def test_landmark_registration():
    from core.data_models import SensedObject

    mem = SpatialMemory(load_config().memory)

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
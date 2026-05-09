from core.data_models import SensorPacket


def test_sensor_packet_defaults():
    s = SensorPacket()

    assert s.delta == 0.016
    assert s.ray_c == 1.0
    assert s.is_real_data is True


def test_sensor_packet_conversion():
    world = {
        "delta": 0.1,
        "ray_c": 0.5,
        "hazard_stim": 1.0,
    }

    packet = SensorPacket.from_world_data(world)

    assert packet.delta == 0.1
    assert packet.ray_c == 0.5
    assert packet.hazard_stim == 1.0
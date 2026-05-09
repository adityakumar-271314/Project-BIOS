from core.telemetry import TickTelemetry


def test_telemetry_to_dict():
    t = TickTelemetry(
        tick=1,
        energy=10,
        integrity=20,
        stress=0,
        fear=0,
        drive=0,
        thrust=0,
        steer=0,
        pos_x=0,
        pos_y=0,
        velocity_x=0,
        velocity_y=0,
        landmark_count=0,
        grid_cells=0,
    )

    d = t.to_dict()

    assert d["energy"] == 10
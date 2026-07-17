from infra.replay import ReplayFrame


def test_replay_frame_to_dict():
    frame = ReplayFrame(
        tick=1,
        sensor_packet={"a": 1},
        motor_output={"b": 2},
    )

    d = frame.to_dict()

    assert d["tick"] == 1

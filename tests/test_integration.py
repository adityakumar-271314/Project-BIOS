from core.agent import Agent
from core.data_models import SensorPacket


def test_full_simulation_loop():
    agent = Agent()

    for _ in range(100):
        sensors = SensorPacket()

        output = agent.tick(
            env_damage=0,
            food=0,
            sensor_data=sensors,
            delta=0.016,
        )

        assert output is not None

    assert agent.bst.is_alive is True
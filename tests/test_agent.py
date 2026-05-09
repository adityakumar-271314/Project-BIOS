from core.agent import Agent
from core.data_models import SensorPacket


def test_agent_tick_runs():
    agent = Agent()

    sensors = SensorPacket()

    output = agent.tick(
        env_damage=0,
        food=0,
        sensor_data=sensors,
        delta=0.016,
    )

    assert output is not None


def test_tick_increments_counter():
    agent = Agent()

    sensors = SensorPacket()

    agent.tick(0, 0, sensors, 0.016)

    assert agent.tick_count == 1
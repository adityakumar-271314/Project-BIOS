import json
from .config_classes import (
    RuntimeConfig,
    SimulationConfig,
    BodyConfig,
    EmotionConfig,
    BrainConfig,
    MemoryConfig,
    BridgeConfig,
)


def load_config(path: str = "config.json") -> SimulationConfig:
    with open(path, "r") as f:
        data = json.load(f)

    # Map the nested dictionaries to their respective dataclasses
    return SimulationConfig(
        simulation=RuntimeConfig(**data["simulation"]),
        body=BodyConfig(**data["body"]),
        emotions=EmotionConfig(**data["emotions"]),
        brain=BrainConfig(**data["brain"]),
        memory=MemoryConfig(**data["memory"]),
        bridge=BridgeConfig(**data["bridge"]),   
    )
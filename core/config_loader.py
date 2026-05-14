"""
Configuration Loader.

Responsible for reading config.json and converting it into structured
SimulationConfig dataclass instances with proper nesting of skill profiles
and subsystem configurations.
"""



import json
from .config_classes import (
    RuntimeConfig,
    SimulationConfig,
    BodyConfig,
    EmotionConfig,
    BrainConfig,
    MemoryConfig,
    BridgeConfig,
    SkillsConfig,
    WanderProfile,
    SeekFoodProfile,
    AvoidHazardProfile,
)


def load_config(path: str = "config.json") -> SimulationConfig:
    with open(path, "r") as f:
        data = json.load(f)

    brain_data = data["brain"]
    skill_data = data["skills"]

    skills = SkillsConfig(
        wander=WanderProfile(
            **skill_data["wander"]
        ),

        seek_food=SeekFoodProfile(
            **skill_data["seek_food"]
        ),

        avoid_hazard=AvoidHazardProfile(
            **skill_data["avoid_hazard"]
        ),
    )

    brain_cfg = BrainConfig(
        **brain_data
    )

    return SimulationConfig(
        simulation=RuntimeConfig(**data["simulation"]),
        body=BodyConfig(**data["body"]),
        emotions=EmotionConfig(**data["emotions"]),
        brain=brain_cfg,
        skills=skills,
        memory=MemoryConfig(**data["memory"]),
        bridge=BridgeConfig(**data["bridge"]),
    )
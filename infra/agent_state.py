from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json


@dataclass#(frozen=True, slots=True)
class AgentState:
    tick_count: int

    energy: float
    integrity: float

    stress: float
    fear: float
    drive: float

    internal_pos_x: float
    internal_pos_y: float

    internal_vel_x: float
    internal_vel_y: float

    is_alive: bool

    rotation: float = 0.0

    @classmethod
    def from_agent(cls, agent) -> "AgentState":
        return cls(
            tick_count=agent.tick_count,

            energy=agent.bst.energy,
            integrity=agent.bst.integrity,

            stress=agent.ehe.stress,
            fear=agent.ehe.fear,
            drive=agent.ehe.drive,

            internal_pos_x=agent.memory.internal_pos.x,
            internal_pos_y=agent.memory.internal_pos.y,

            internal_vel_x=agent.memory.internal_vel.x,
            internal_vel_y=agent.memory.internal_vel.y,

            is_alive=agent.bst.is_alive,

            rotation=getattr(agent, "rotation", 0.0),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=4)

    @classmethod
    def load(cls, path: Path) -> "AgentState":
        with open(path, "r", encoding="utf-8") as f:
            return cls(**json.load(f))
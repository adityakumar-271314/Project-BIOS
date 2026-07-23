from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json

from infra.agent_state import AgentState


@dataclass
class WorldState:
    run_id: int
    world_seed: int
    continuation: bool = False

    consumed_food_ids: list[int] = field(default_factory=list)

    agent_state: AgentState | None = None

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "run_id": self.run_id,
            "world_seed": self.world_seed,
            "continuation": self.continuation,
            "consumed_food_ids": self.consumed_food_ids,
            "agent_state": (self.agent_state.__dict__ if self.agent_state else None),
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @classmethod
    def load(cls, path: Path) -> "WorldState":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        agent_data = data.get("agent_state")

        if agent_data:
            data["agent_state"] = AgentState(**agent_data)

        return cls(**data)

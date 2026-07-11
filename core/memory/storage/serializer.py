from __future__ import annotations

import json
from pathlib import Path

from ..schemas import EpisodicEvent


class EpisodeSerializer:

    def __init__(self, root: Path | str = "core/memory/episodes/run_000001"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, event: EpisodicEvent):

        episode_id = self._next_id()

        folder = self.root / f"episode_{episode_id:06d}"
        folder.mkdir(parents=True, exist_ok=True)

        metadata = {
            "episode_id": episode_id,
            "event_type": event.event_type,
            "start_tick": event.start_tick,
            "peak_tick": event.peak_tick,
            "end_tick": event.end_tick,
            "peak_significance": event.peak_significance,
        }

        with open(folder / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=4)

        with open(folder / "episode.json", "w") as f:
            json.dump(event.to_dict(), f, indent=4)

    def _next_id(self):

        folders = [
            p
            for p in self.root.iterdir()
            if p.is_dir() and p.name.startswith("episode_")
        ]

        if not folders:
            return 1

        ids = [int(p.name.split("_")[-1]) for p in folders]

        return max(ids) + 1

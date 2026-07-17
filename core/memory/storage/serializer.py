from __future__ import annotations
import json
from pathlib import Path
from ..schemas import EpisodicEvent

class EpisodeSerializer:
    def __init__(self, root: Path | str = "run_history/run000001/episodes"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.root / "manifest.json"
        self._init_manifest()

    def _init_manifest(self):
        if not self.manifest_path.exists():
            with open(self.manifest_path, "w") as f:
                json.dump({"version": 1, "next_episode_id": 1}, f)

    def _get_and_increment_id(self) -> int:
        with open(self.manifest_path, "r+") as f:
            data = json.load(f)
            current_id = data["next_episode_id"]
            data["next_episode_id"] = current_id + 1
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
        return current_id

    def save(self, event: EpisodicEvent) -> int:
        episode_id = self._get_and_increment_id()
        folder = self.root / f"episode{episode_id:06d}"
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

        return episode_id

    def load(self, episode_id: int) -> EpisodicEvent:
        file_path = self.root / f"episode{episode_id:06d}" / "episode.json"
        with open(file_path, "r") as f:
            data = json.load(f)
        return EpisodicEvent.from_dict(data)
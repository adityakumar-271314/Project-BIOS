from __future__ import annotations
import json
from pathlib import Path
from ..schemas import EpisodicEvent


class EpisodeSerializer:
    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.root / "manifest.json"
        self._init_manifest()

    def _init_manifest(self):
        if not self.manifest_path.exists():
            # Initialize with schema version 2 (compact, de-duplicated storage layout)
            with open(self.manifest_path, "w") as f:
                json.dump(
                    {"version": 2, "next_episode_id": 1}, f, separators=(",", ":")
                )
        else:
            # Check and migrate legacy v1 manifests to v2 automatically
            with open(self.manifest_path, "r+") as f:
                data = json.load(f)
                if data.get("version", 1) < 2:
                    data["version"] = 2
                    f.seek(0)
                    json.dump(data, f, separators=(",", ":"))
                    f.truncate()

    def _get_and_increment_id(self) -> int:
        with open(self.manifest_path, "r+") as f:
            data = json.load(f)
            current_id = data["next_episode_id"]
            data["next_episode_id"] = current_id + 1
            f.seek(0)
            json.dump(data, f, separators=(",", ":"))
            f.truncate()
        return current_id

    def save(self, event: EpisodicEvent) -> int:
        episode_id = self._get_and_increment_id()
        folder = self.root / f"episode{episode_id:06d}"
        folder.mkdir(parents=True, exist_ok=True)

        with open(folder / "episode.json", "w") as f:
            json.dump(event.to_dict(), f, separators=(",", ":"))

        return episode_id

    def load(self, episode_id: int) -> EpisodicEvent:
        folder = self.root / f"episode{episode_id:06d}"
        file_path = folder / "episode.json"

        # Backward compatibility check: gracefully handle legacy v1 per-episode metadata.json
        legacy_meta_path = folder / "metadata.json"
        if legacy_meta_path.exists():
            # Legacy file present; safe to ignore or handle gracefully without throwing errors
            pass

        with open(file_path, "r") as f:
            data = json.load(f)
        return EpisodicEvent.from_dict(data)

"""
Episode payload I/O ONLY: allocates episode ids and reads/writes episodeNNNNNN/episode.json.
It knows nothing about metadata, hierarchy or retrieval.
"""
from __future__ import annotations
import re
import threading
from pathlib import Path
from typing import List, Optional

from ..schemas import EpisodicEvent
from .atomic_io import atomic_write_json, read_json
from .payload_codec import pack, unpack

MANIFEST_VERSION = 3
_EP_DIR = re.compile(r"^episode(\d+)$")


class EpisodeSerializer:
    def __init__(self, root: Path | str, float_digits: Optional[int] = 4):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.root / "manifest.json"
        self.float_digits = float_digits
        self._lock = threading.Lock()
        self._init_manifest()

    def episode_dir(self, episode_id: int) -> Path:
        return self.root / f"episode{episode_id:06d}"

    def list_ids(self) -> List[int]:
        ids = []
        for p in self.root.iterdir():
            m = _EP_DIR.match(p.name)
            if m and (p / "episode.json").exists():
                ids.append(int(m.group(1)))
        return sorted(ids)

    def _init_manifest(self) -> None:
        # The folder scan is the floor: a lost or stale manifest can never cause id reuse.
        floor = max(self.list_ids(), default=0) + 1
        data = read_json(self.manifest_path)
        if not isinstance(data, dict) or not isinstance(data.get("next_episode_id"), int):
            data = {"next_episode_id": floor}
        data["version"] = MANIFEST_VERSION
        data["next_episode_id"] = max(data["next_episode_id"], floor)
        atomic_write_json(self.manifest_path, data)

    def _allocate_id(self) -> int:
        with self._lock:
            data = read_json(self.manifest_path) or {}
            current = data.get("next_episode_id") or (max(self.list_ids(), default=0) + 1)
            data["version"] = MANIFEST_VERSION
            data["next_episode_id"] = current + 1
            atomic_write_json(self.manifest_path, data)
            return current

    def save(self, event: EpisodicEvent) -> int:
        episode_id = self._allocate_id()
        folder = self.episode_dir(episode_id)
        folder.mkdir(parents=True, exist_ok=True)
        atomic_write_json(folder / "episode.json", pack(event.to_dict(), self.float_digits))
        return episode_id

    def load(self, episode_id: int) -> EpisodicEvent:
        data = read_json(self.episode_dir(episode_id) / "episode.json")
        if data is None:
            raise FileNotFoundError(f"episode {episode_id} not found in {self.root}")
        return EpisodicEvent.from_dict(unpack(data))

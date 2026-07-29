from __future__ import annotations
import math
from pathlib import Path
from .schemas import EpisodicEvent
from .storage.episode_archive import EpisodeArchive

"""
Episodic Memory System.

Encodes emotionally salient and statistically surprising
experiences into sparse autobiographical memories.

Online mean/variance tracker using Welford's algorithm.

Used to estimate what constitutes "normal" experience so the
agent can detect statistically surprising state transitions.
"""


class RunningStats:
    def __init__(self):
        self.n = 0
        self.mean = 0.0
        self.M2 = 0.0

    def update(self, value: float) -> None:
        self.n += 1
        delta = value - self.mean
        self.mean += delta / self.n
        self.M2 += delta * (value - self.mean)

    @property
    def variance(self) -> float:
        return self.M2 / (self.n - 1) if self.n > 1 else 0.0

    @property
    def std(self) -> float:
        return math.sqrt(self.variance)


class EpisodicMemory:
    def __init__(self, config):
        self.cfg = config
        self._tick = 0
        self.archive = EpisodeArchive(
            root_dir=getattr(config, "episode_root", "core/memory/episodes")
        )
        self.stats = {
            "energy_delta": RunningStats(),
            "integrity_delta": RunningStats(),
            "stress_delta": RunningStats(),
            "fear_delta": RunningStats(),
            "drive_delta": RunningStats(),
        }

    def initialize_run_state(
        self,
        continuation: bool,
        episodes_dir: Path | str | None = None,
    ) -> None:
        if episodes_dir:
            self.archive = EpisodeArchive(root_dir=Path(episodes_dir))

        if not continuation:
            self._tick = 0
            self.stats = {
                "energy_delta": RunningStats(),
                "integrity_delta": RunningStats(),
                "stress_delta": RunningStats(),
                "fear_delta": RunningStats(),
                "drive_delta": RunningStats(),
            }

    def update(self) -> None:
        self._tick += 1

    def update_stats(self, deltas: dict) -> None:
        """Causal execution principle: Updates running statistics with frame deltas."""
        for key, value in deltas.items():
            if key in self.stats:
                self.stats[key].update(value)

    def encode(self, event: EpisodicEvent) -> None:
        if not isinstance(event, EpisodicEvent):
            raise TypeError(
                f"EpisodicMemory.encode expected EpisodicEvent, got {type(event)}"
            )
        self.archive.save(event)

    def export_state(self) -> dict:
        return {"tick": self._tick, "index": self.archive.index.data}

    def import_state(self, data: dict) -> None:
        self._tick = data.get("tick", 0)
        if "index" in data:
            self.archive.index.data = data["index"]
            self.archive.index.save()

    def get_events(self) -> tuple[EpisodicEvent, ...]:
        episodes_meta = self.archive.index.data["episodes"]
        return tuple(self.archive.load(m["id"]) for m in episodes_meta)

    def get_debug_memories(self) -> list[dict]:
        return [dict(m) for m in self.archive.index.data["episodes"]]

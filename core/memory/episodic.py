"""
EpisodicMemory: thin facade. It wires the pieces of ONE run together and exposes the API the
rest of the agent uses. No algorithms live here:

    storage/            EpisodeArchive  (payloads + metadata rows, crash-safe, de-dup)
    episode_hierarchy/  HierarchyEngine (bouts + schemas), HierarchyRetriever, SimilarityEngine
    consolidation/      DeferredGrouper (when to consolidate), HomeostasisEvaluator (is it calm)
    stats.py            RunningStats

Each run owns one folder (runXXXX/episodes); the run id is that folder's name.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .episode_hierarchy.engine import HierarchyEngine
from .episode_hierarchy.retriever import HierarchyRetriever, RecallQuery
from .schemas import EpisodicEvent
from .stats import (
    RunningStats,
    new_stats_bank,
)  # noqa: F401  (RunningStats re-exported)
from .storage.episode_archive import EpisodeArchive


class EpisodicMemory:
    def __init__(self, config):
        self.cfg = config
        self._tick = 0
        self.stats = new_stats_bank()
        self._listeners: List[Callable[[int], None]] = []
        self._open(Path(getattr(config, "episode_root", "core/memory/episodes")))

    # ---------- wiring ----------
    def _open(self, root: Path) -> None:
        self.archive = EpisodeArchive(root_dir=root)
        self.hierarchy = HierarchyEngine(root, run_id=self.archive.run_id)
        self.hierarchy.catch_up(
            self.archive.index
        )  # repairs missing/old hierarchy files
        self.hierarchy.save()

    @property
    def run_id(self) -> str:
        return self.archive.run_id

    def subscribe_encoded(self, callback: Callable[[int], None]) -> None:
        """callback(episode_id) fires for every newly stored episode (not for duplicates)."""
        self._listeners.append(callback)

    def initialize_run_state(
        self, continuation: bool, episodes_dir: Path | str | None = None
    ) -> None:
        if episodes_dir:
            self._open(Path(episodes_dir))
        if not continuation:
            self._tick = 0
            self.stats = new_stats_bank()

    # ---------- per-tick ----------
    def update(self) -> None:
        self._tick += 1

    def update_stats(self, deltas: dict) -> None:
        for key, value in deltas.items():
            if key in self.stats:
                self.stats[key].update(value)

    # ---------- write ----------
    def encode(self, event: EpisodicEvent) -> Optional[int]:
        if not isinstance(event, EpisodicEvent):
            raise TypeError(
                f"EpisodicMemory.encode expected EpisodicEvent, got {type(event)}"
            )
        episode_id, created = self.archive.save_ex(event)
        if created:
            for callback in self._listeners:
                callback(episode_id)
        return episode_id

    def consolidate(self, episode_ids: List[int]) -> int:
        rows = [r for r in (self.archive.index.get(i) for i in episode_ids) if r]
        applied = self.hierarchy.update(rows)
        self.hierarchy.save()
        return applied

    def save_hierarchy(self) -> None:
        self.hierarchy.save()

    # ---------- read ----------
    def meta(self, episode_id: int) -> Optional[Dict[str, Any]]:
        return self.archive.index.get(episode_id)

    def retrieve_top_down(
        self,
        target_goal: Optional[str] = None,
        target_skill: Optional[str] = None,
        nearest_landmark_id: Optional[int] = None,
        min_quality: float = 0.25,
        top_k: int = 5,
        x: Optional[float] = None,
        y: Optional[float] = None,
    ) -> List[EpisodicEvent]:
        retriever = HierarchyRetriever(
            self.archive.index,
            self.hierarchy.state,
            similarity=self.hierarchy.episode_sim,
        )
        ids = retriever.retrieve(
            RecallQuery(
                goal=target_goal,
                skill=target_skill,
                landmark=nearest_landmark_id,
                x=x,
                y=y,
                min_quality=min_quality,
                top_k=top_k,
            )
        )
        return [self.archive.load(i) for i in ids]

    def get_events(self) -> tuple[EpisodicEvent, ...]:
        return tuple(self.archive.load(r["id"]) for r in self.archive.index.rows)

    def get_debug_memories(self) -> list[dict]:
        return [dict(r) for r in self.archive.index.rows]

    # ---------- checkpoint ----------
    def export_state(self) -> dict:
        """Index and hierarchy live on disk in the run folder; the checkpoint only needs pointers."""
        return {
            "tick": self._tick,
            "run_id": self.run_id,
            "episode_dir": str(self.archive.root),
            "episodes": len(self.archive.index),
            "hierarchy": self.hierarchy.summary(),
        }

    def import_state(self, data: dict) -> None:
        self._tick = data.get("tick", 0)

from __future__ import annotations
import math
from pathlib import Path
from typing import List, Optional
from .schemas import EpisodicEvent
from .storage.episode_archive import EpisodeArchive
from .episode_hierarchy.retriever import HierarchyRetriever


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
    """
    Episodic Memory System.
    Encodes emotionally salient and statistically surprising experiences into sparse autobiographical memories,
    backed by a multi-tier hierarchical index and zero-load retrieval[cite: 1].
    """
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
        for key, value in deltas.items():
            if key in self.stats:
                self.stats[key].update(value)

    def encode(self, event: EpisodicEvent) -> None:
        if not isinstance(event, EpisodicEvent):
            raise TypeError(
                f"EpisodicMemory.encode expected EpisodicEvent, got {type(event)}"
            )
        self.archive.save(event)

    def retrieve_top_down(
        self,
        target_goal: Optional[str] = None,
        target_skill: Optional[str] = None,
        nearest_landmark_id: Optional[int] = None,
        min_quality: float = 0.25,
        top_k: int = 5
    ) -> List[EpisodicEvent]:
        """
        Executes zero-load top-down coarse-to-fine retrieval over the unified memory index
        and loads full episode payloads strictly for the final top-ranked candidates.
        """
        from core.memory.episode_hierarchy.retriever import HierarchyRetriever
        
        retriever = HierarchyRetriever(
            unified_index_data=self.archive.index.data
        )
        ranked_episode_ids = retriever.zero_load_retrieve_candidates(
            target_goal=target_goal,
            target_skill=target_skill,
            nearest_landmark_id=nearest_landmark_id,
            min_quality=min_quality,
            top_k=top_k
        )
        return [self.archive.load(eid) for eid in ranked_episode_ids]

    export_state = lambda self: {
        "tick": self._tick,
        "index": self.archive.index.data,
        "hierarchy": self.archive.hierarchy_index.graph_state.to_dict()
    }

    def import_state(self, data: dict) -> None:
        """
        Imports memory state into the unified index store, supporting 
        both flat metadata and asynchronous/cached hierarchy summaries.
        """
        self._tick = data.get("tick", 0)
        
        # Handle unified index payload import
        if "index" in data:
            self.archive.index.data = data["index"]
            self.archive.index.save()
        elif "unified_index" in data:
            self.archive.index.data = data["unified_index"]
            self.archive.index.save()
            
        # Backward compatibility / fallback: if legacy 'hierarchy' data is passed in state,
        # map it cleanly into the unified index's 'hierarchies' field without separate files.
        if "hierarchy" in data:
            hierarchy_dict = data["hierarchy"]
            # If it's a serialized graph state object or dict, extract hierarchies safely
            if hasattr(hierarchy_dict, "to_dict"):
                hierarchies_data = hierarchy_dict.to_dict().get("hierarchies", {})
            elif isinstance(hierarchy_dict, dict):
                hierarchies_data = hierarchy_dict.get("hierarchies", hierarchy_dict)
            else:
                hierarchies_data = {}
                
            self.archive.index.data["hierarchies"] = hierarchies_data
            self.archive.index.save()

    def get_events(self) -> tuple[EpisodicEvent, ...]:
        episodes_meta = self.archive.index.data["episodes"]
        return tuple(self.archive.load(m["id"]) for m in episodes_meta)

    def get_debug_memories(self) -> list[dict]:
        return [dict(m) for m in self.archive.index.data["episodes"]]
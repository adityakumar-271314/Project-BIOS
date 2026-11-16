from pathlib import Path
from collections import OrderedDict
from .serializer import EpisodeSerializer
from .metadata_index import MetadataIndex
from ..schemas import EpisodicEvent
from typing import List
import math


class EpisodeArchive:
    """
    Manages isolated episode payload serialization (`episode.json`) and a single
    unified metadata/hierarchy index (`memory_index.json`), removing multi-file redundancy.
    """
    def __init__(self, root_dir: Path | str, cache_size: int = 128):
        self.root = Path(root_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.serializer = EpisodeSerializer(root=self.root)
        
        # Unified index combining episodes and optional group/hierarchy summaries
        self.index = MetadataIndex(self.root / "memory_index.json")
        
        self.cache = OrderedDict()
        self.cache_size = cache_size

    def save(self, event: EpisodicEvent) -> int:
        """
        Saves episode payload and appends lean metadata strictly to the unified index.
        Synchronous hierarchy graph building has been removed from the write path.
        """
        episode_id = self.serializer.save(event)
        episode_id_str = f"episode_{episode_id:06d}"

        meta = {
            "id": episode_id,
            "node_id": episode_id_str,
            "event_type": event.event_type,
            "start_tick": event.start_tick,
            "end_tick": event.end_tick,
            "peak_tick": event.peak_tick,
            "peak_significance": event.peak_significance,
            "peak_x": event.peak_x,
            "peak_y": event.peak_y,
            "dominant_goal": event.signature.dominant_goal,
            "dominant_skill": event.signature.dominant_skill,
            "outcome_status": event.signature.outcome_status.value if hasattr(event.signature.outcome_status, "value") else event.signature.outcome_status,
            "overall_quality": event.quality.overall_quality if event.quality else 1.0,
            "nearest_landmark_id": event.signature.nearest_landmark_id,
        }
        
        # Append to unified index and save atomically
        self.index.add(meta)

        self._cache_put(episode_id, event)
        return episode_id
    
    def load(self, episode_id: int) -> EpisodicEvent:
        if episode_id in self.cache:
            self.cache.move_to_end(episode_id)
            return self.cache[episode_id]

        event = self.serializer.load(episode_id)
        self._cache_put(episode_id, event)
        return event

    def _cache_put(self, episode_id: int, event: EpisodicEvent):
        self.cache[episode_id] = event
        if len(self.cache) > self.cache_size:
            self.cache.popitem(last=False)

    def recall_latest(self) -> EpisodicEvent | None:
        meta = self.index.query_latest()
        return self.load(meta["id"]) if meta else None

    def recall_near(
        self, pos_x: float, pos_y: float, radius: float
    ) -> List[EpisodicEvent]:
        matched_ids = []
        for meta in self.index.data.get("episodes", []):
            px = meta.get("peak_x", 0.0)
            py = meta.get("peak_y", 0.0)
            dist = math.hypot(px - pos_x, py - pos_y)
            if dist <= radius:
                matched_ids.append(meta["id"])
        return [self.load(eid) for eid in matched_ids]
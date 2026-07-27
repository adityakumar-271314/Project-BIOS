from pathlib import Path
from collections import OrderedDict
from .serializer import EpisodeSerializer
from .metadata_index import MetadataIndex
from ..schemas import EpisodicEvent


class EpisodeArchive:
    def __init__(self, root_dir: Path | str, cache_size: int = 128):
        self.root = Path(root_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.serializer = EpisodeSerializer(root=self.root)
        self.index = MetadataIndex(self.root / "metadata_index.json")
        self.cache = OrderedDict()
        self.cache_size = cache_size

    def save(self, event: EpisodicEvent):
        # Persist full episode data (including immutable signature) to disk
        episode_id = self.serializer.save(event)

        # Extract minimal index metadata using the revised EpisodeSignature attributes
        sig = event.signature
        meta = {
            "id": episode_id,
            "event_type": event.event_type,
            "peak_tick": event.peak_tick,
            "peak_significance": event.peak_significance,
            "peak_x": event.peak_x,
            "peak_y": event.peak_y,
            "landmark_interactions": sig.landmark_interactions,
            "goal_transitions": len(sig.goal_transitions),
            "skill_transitions": len(sig.skill_transitions),
            "primary_drivers": list(sig.primary_importance_drivers),
        }
        self.index.add(meta)

        # Cache live instance
        self._cache_put(episode_id, event)

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
    ) -> list[EpisodicEvent]:
        r_sq = radius * radius
        matches = []
        for meta in self.index.data["episodes"]:
            dx = meta["peak_x"] - pos_x
            dy = meta["peak_y"] - pos_y
            if (dx * dx + dy * dy) <= r_sq:
                matches.append(self.load(meta["id"]))
        return matches
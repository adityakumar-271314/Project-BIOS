"""
Archive facade for ONE run folder: payload store (serializer) + metadata rows (index).

Role: save/load episodes, keep the two in sync, repair drift, de-duplicate re-detections,
position recall. It does NOT group episodes (that is episode_hierarchy) and does NOT decide
when to consolidate (that is consolidation).
"""
from __future__ import annotations
from collections import OrderedDict
from pathlib import Path
from typing import List, Optional, Tuple

from ..schemas import EpisodicEvent, EpisodeMeta
from .metadata_index import MetadataIndex
from .serializer import EpisodeSerializer


class EpisodeArchive:
    def __init__(
        self,
        root_dir: Path | str,
        cache_size: int = 128,
        dedupe_iou: Optional[float] = 0.6,
        dedupe_growth: float = 1.2,
        float_digits: Optional[int] = 4,
    ):
        self.root = Path(root_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.serializer = EpisodeSerializer(self.root, float_digits=float_digits)
        self.index = MetadataIndex(self.root)
        self.cache: "OrderedDict[int, EpisodicEvent]" = OrderedDict()
        self.cache_size = cache_size
        self.dedupe_iou = dedupe_iou
        self.dedupe_growth = dedupe_growth
        self.reconcile()

    @property
    def run_id(self) -> str:
        return self.index.run_id

    # ---------- write ----------
    def save(self, event: EpisodicEvent) -> int:
        return self.save_ex(event)[0]

    def save_ex(self, event: EpisodicEvent) -> Tuple[int, bool]:
        """Returns (episode_id, created). created=False means an equivalent episode existed."""
        dup = self.find_duplicate(event)
        if dup is not None:
            return dup, False
        episode_id = self.serializer.save(event)
        self.index.add(EpisodeMeta.from_event(event, episode_id).to_dict())
        self._cache_put(episode_id, event)
        return episode_id, True

    def find_duplicate(self, event: EpisodicEvent) -> Optional[int]:
        """
        Overlapping detection windows can re-detect the same real episode. Same goal+skill
        and high time-IoU, without being clearly longer (a fuller version), counts as a duplicate.
        """
        if self.dedupe_iou is None:
            return None
        t0, t1 = event.start_tick, event.end_tick
        dur = max(1, t1 - t0 + 1)
        goal, skill = event.signature.dominant_goal, event.signature.dominant_skill
        for row in self.index.overlapping(t0, t1):
            if row.get("dominant_goal") != goal or row.get("dominant_skill") != skill:
                continue
            r0, r1 = row.get("start_tick", 0), row.get("end_tick", 0)
            rdur = max(1, r1 - r0 + 1)
            inter = min(t1, r1) - max(t0, r0) + 1
            union = dur + rdur - inter
            if inter > 0 and inter / union >= self.dedupe_iou and dur <= rdur * self.dedupe_growth:
                return row["id"]
        return None

    # ---------- read ----------
    def load(self, episode_id: int) -> EpisodicEvent:
        if episode_id in self.cache:
            self.cache.move_to_end(episode_id)
            return self.cache[episode_id]
        event = self.serializer.load(episode_id)
        self._cache_put(episode_id, event)
        return event

    def _cache_put(self, episode_id: int, event: EpisodicEvent) -> None:
        self.cache[episode_id] = event
        self.cache.move_to_end(episode_id)
        while len(self.cache) > self.cache_size:
            self.cache.popitem(last=False)

    def recall_latest(self) -> Optional[EpisodicEvent]:
        meta = self.index.query_latest()
        return self.load(meta["id"]) if meta else None

    def recall_near(self, pos_x: float, pos_y: float, radius: float) -> List[EpisodicEvent]:
        return [self.load(r["id"]) for r in self.index.near(pos_x, pos_y, radius)]

    # ---------- repair ----------
    def reconcile(self) -> int:
        """Index any episode folder that has no metadata row (e.g. crash between the two writes)."""
        missing = [i for i in self.serializer.list_ids() if i not in self.index.by_id]
        for episode_id in missing:
            event = self.serializer.load(episode_id)
            self.index.add(EpisodeMeta.from_event(event, episode_id).to_dict())
        return len(missing)

    def rebuild_index(self) -> int:
        """Throw the metadata index away and rebuild it from the episode folders."""
        self.index.reset()
        return self.reconcile()

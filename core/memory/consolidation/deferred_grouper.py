from __future__ import annotations
from typing import List, Optional
from ..schemas import EpisodicEvent, EpisodeMeta
from ..episode_hierarchy.grouper import LazyGrouper


class DeferredGrouper:
    """
    Staging queue and batch flush worker for hierarchy groups. Accepts EpisodicEvents,
    strips them to lean EpisodeMeta descriptors, and passes them to LazyGrouper 
    when commanded by the pipeline.
    """
    def __init__(self, metadata_index, grouper: Optional[LazyGrouper] = None):
        self.metadata_index = metadata_index
        self.grouper = grouper or LazyGrouper()
        self.staging_queue: List[EpisodeMeta] = []

    def stage_episode(self, event: EpisodicEvent, episode_id: Optional[int] = None) -> None:
        meta = EpisodeMeta.from_event(event, episode_id=episode_id)
        self.staging_queue.append(meta)

    @property
    def has_pending(self) -> bool:
        return len(self.staging_queue) > 0

    def flush_groups(self) -> int:
        """Executes batch grouping on staged items and flushes to the unified index."""
        if not self.staging_queue:
            return 0

        existing_hierarchies = self.metadata_index.data.get("hierarchies", {})
        next_idx = len(existing_hierarchies) + 1

        new_groups = self.grouper.cluster(
            episodes=self.staging_queue,
            start_index=next_idx,
            prefix="group",
        )

        for gid, summary in new_groups.items():
            existing_hierarchies[gid] = summary.to_dict()

        count = len(self.staging_queue)
        self.staging_queue.clear()
        self.metadata_index.update_hierarchies(existing_hierarchies)
        return count
"""
DeferredGrouper: the consolidation SCHEDULER. Holds a queue of episode ids and decides when
to hand them to the hierarchy; it contains no grouping logic and no storage code.

  * Episodes are staged by ID the moment EpisodicMemory.encode() saves them (subscription),
    so queue ids can never disagree with archive ids.
  * It talks to EpisodicMemory (stable object) and looks up the archive/hierarchy at call
    time, so swapping run folders cannot leave it writing into an orphaned index.
  * maybe_flush(): flush when calm (safe) OR when overdue (too many pending / too old), so
    consolidation can never starve; each flush is capped by a per-call budget.
  * finalize(): flush everything and persist; call it at run end / checkpoint.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass(slots=True)
class ConsolidationPolicy:
    max_pending: int = 16
    max_staleness_ticks: int = 1200
    budget_per_flush: int = 32


class DeferredGrouper:
    def __init__(self, episodic_memory, policy: Optional[ConsolidationPolicy] = None):
        self.memory = episodic_memory
        self.policy = policy or ConsolidationPolicy()
        self._queue: List[int] = []
        episodic_memory.subscribe_encoded(self.stage)

    def stage(self, episode_id: int) -> None:
        if episode_id not in self._queue:
            self._queue.append(episode_id)

    @property
    def pending_count(self) -> int:
        return len(self._queue)

    @property
    def has_pending(self) -> bool:
        return bool(self._queue)

    def is_overdue(self, now_tick: int) -> bool:
        if not self._queue:
            return False
        if len(self._queue) >= self.policy.max_pending:
            return True
        oldest = self.memory.meta(self._queue[0])
        return bool(oldest) and (now_tick - oldest.get("end_tick", now_tick)) >= self.policy.max_staleness_ticks

    def maybe_flush(self, safe: bool, now_tick: int) -> int:
        if not self._queue:
            return 0
        if safe or self.is_overdue(now_tick):
            return self.flush(self.policy.budget_per_flush)
        return 0

    def flush(self, budget: Optional[int] = None) -> int:
        batch = self._queue if budget is None else self._queue[:budget]
        ids = list(batch)
        del self._queue[: len(ids)]
        return self.memory.consolidate(ids) if ids else 0

    def finalize(self) -> int:
        total = self.flush(None)
        self.memory.save_hierarchy()
        return total

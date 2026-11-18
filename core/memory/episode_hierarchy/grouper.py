"""
HierarchyBuilder: pure, incremental grouping logic. No I/O, no scheduling.

add(state, row) places ONE episode row (in archive-id order) into
  * a bout    : extends the open bout if close in time AND the same activity, else closes it
                and opens a new one (closed bouts never change again);
  * a schema  : joins the most similar existing schema, else founds a new one.
It is idempotent (ids <= state.watermark are skipped) and order-deterministic, so replaying
all rows from scratch yields exactly the state built incrementally.
All similarity decisions are delegated to SimilarityEngine.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .nodes import HierarchyNode, HierarchyState
from .similarity import BOUT_WEIGHTS, EPISODE_WEIGHTS, EpisodeFeatures, SimilarityEngine


@dataclass(slots=True)
class GrouperConfig:
    bout_max_gap: int = 300       # ticks between end of bout and start of next episode
    bout_link: float = 0.55       # min bout-similarity to continue a bout
    schema_join: float = 0.62     # min episode-similarity to join an existing schema


class HierarchyBuilder:
    def __init__(
        self,
        config: Optional[GrouperConfig] = None,
        episode_sim: Optional[SimilarityEngine] = None,
        bout_sim: Optional[SimilarityEngine] = None,
    ):
        self.cfg = config or GrouperConfig()
        self.episode_sim = episode_sim or SimilarityEngine(EPISODE_WEIGHTS)
        self.bout_sim = bout_sim or SimilarityEngine(BOUT_WEIGHTS)

    def add(self, state: HierarchyState, row: Dict[str, Any]) -> bool:
        eid = row["id"]
        if eid <= state.watermark:
            return False
        feat = EpisodeFeatures.from_row(row)
        self._place_in_bout(state, row, feat)
        self._place_in_schema(state, row, feat)
        state.watermark = eid
        return True

    def _place_in_bout(self, state: HierarchyState, row: Dict[str, Any], feat: EpisodeFeatures) -> None:
        bout = state.bouts.get(state.open_bout) if state.open_bout else None
        if bout is not None:
            gap = row.get("start_tick", 0) - bout.end_tick
            if (gap <= self.cfg.bout_max_gap
                    and self.bout_sim.score(feat, bout.prototype) >= self.cfg.bout_link):
                bout.add(row, feat)
                return
            bout.closed = True
        node_id = f"bout_{state.next_bout:05d}"
        state.next_bout += 1
        bout = HierarchyNode(node_id=node_id, level="bout")
        bout.add(row, feat)
        state.bouts[node_id] = bout
        state.open_bout = node_id

    def _place_in_schema(self, state: HierarchyState, row: Dict[str, Any], feat: EpisodeFeatures) -> None:
        best: Optional[HierarchyNode] = None
        best_score = 0.0
        for schema in state.schemas.values():
            s = self.episode_sim.score(feat, schema.prototype)
            if s > best_score:
                best, best_score = schema, s
        if best is not None and best_score >= self.cfg.schema_join:
            best.add(row, feat)
            return
        node_id = f"schema_{state.next_schema:05d}"
        state.next_schema += 1
        schema = HierarchyNode(node_id=node_id, level="schema")
        schema.add(row, feat)
        state.schemas[node_id] = schema

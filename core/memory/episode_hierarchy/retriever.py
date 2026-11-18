"""
HierarchyRetriever: top-down recall. Reads the index and the hierarchy; builds nothing.

1. Coarse : score schema prototypes against the query, keep the best few (plus episodes not
            yet consolidated, so fresh memories are never invisible).
2. Fine   : rank member episodes with SimilarityEngine + quality + significance + recency.
Everything is soft-scored; the only exclusion is a known goal mismatch (similarity veto),
so a missing landmark or skill never hides an otherwise good episode.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Optional, Set

from ..storage.metadata_index import MetadataIndex
from .nodes import HierarchyState
from .similarity import EpisodeFeatures, SimilarityEngine, _s


@dataclass(slots=True)
class RecallQuery:
    goal: Optional[str] = None
    skill: Optional[str] = None
    event_type: Optional[str] = None
    landmark: Optional[int] = None
    x: Optional[float] = None
    y: Optional[float] = None
    min_quality: float = 0.25
    top_k: int = 5


@dataclass(slots=True)
class RetrievalConfig:
    schema_fanout: int = 3
    w_similarity: float = 0.45
    w_quality: float = 0.20
    w_significance: float = 0.20
    w_recency: float = 0.15
    recency_scale: float = 5000.0     # ticks


class HierarchyRetriever:
    def __init__(
        self,
        index: MetadataIndex,
        state: HierarchyState,
        similarity: Optional[SimilarityEngine] = None,
        config: Optional[RetrievalConfig] = None,
    ):
        self.index = index
        self.state = state
        self.sim = similarity or SimilarityEngine()
        self.cfg = config or RetrievalConfig()

    def candidate_ids(self, qf: EpisodeFeatures, top_k: int) -> Set[int]:
        scored = []
        for schema in self.state.schemas.values():
            s = self.sim.score(qf, schema.prototype, penalize_missing=False)
            if s > 0.0:
                scored.append((-s, schema.node_id, schema))
        scored.sort(key=lambda t: (t[0], t[1]))
        ids: Set[int] = set()
        for _, _, schema in scored[: self.cfg.schema_fanout]:
            ids.update(schema.episode_ids)
        ids.update(r["id"] for r in self.index.rows_after(self.state.watermark))
        if len(ids) < top_k:                       # hierarchy too thin: widen to everything
            ids = set(self.index.by_id)
        return ids

    def retrieve(self, query: RecallQuery) -> List[int]:
        qf = EpisodeFeatures(
            goal=_s(query.goal), skill=_s(query.skill), event_type=_s(query.event_type),
            landmark=_s(query.landmark), x=query.x, y=query.y,
        )
        max_sig = max(self.index.max_significance, 1e-9)
        latest = self.index.latest_tick
        ranked = []
        for eid in self.candidate_ids(qf, query.top_k):
            row = self.index.by_id[eid]
            quality = row.get("overall_quality", 1.0)
            if quality < query.min_quality:
                continue
            feat = EpisodeFeatures.from_row(row)
            if self.sim.vetoed(qf, feat):
                continue
            sim = self.sim.score(qf, feat, penalize_missing=False)
            sig = min(1.0, row.get("peak_significance", 0.0) / max_sig)
            recency = math.exp(-max(0, latest - row.get("end_tick", 0)) / self.cfg.recency_scale)
            score = (self.cfg.w_similarity * sim + self.cfg.w_quality * quality
                     + self.cfg.w_significance * sig + self.cfg.w_recency * recency)
            ranked.append((score, eid))
        ranked.sort(key=lambda t: (-t[0], -t[1]))
        return [eid for _, eid in ranked[: query.top_k]]

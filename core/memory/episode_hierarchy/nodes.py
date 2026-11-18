"""
Data model of the hierarchy (plain data, no behaviour beyond bookkeeping, no I/O).

    Run (root, implicit: one memory folder = one run)
     +-- Bout    : temporally contiguous episodes doing the same activity   (time tree)
     +-- Schema  : episodes of the same kind recurring anywhere in the run   (recurrence)
         each node keeps aggregate statistics, an exemplar, and member episode ids.

Members are always ARCHIVE episode ids (ints), never ticks.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .similarity import CATEGORICAL, EpisodeFeatures


@dataclass
class GroupAgg:
    counts: Dict[str, Dict[str, int]] = field(default_factory=dict)
    n: int = 0
    sum_x: float = 0.0
    sum_y: float = 0.0
    sum_hazard: float = 0.0
    sum_quality: float = 0.0
    max_significance: float = 0.0

    def add(self, f: EpisodeFeatures, quality: float, significance: float) -> None:
        for name in CATEGORICAL:
            v = getattr(f, name)
            if v is not None:
                d = self.counts.setdefault(name, {})
                d[v] = d.get(v, 0) + 1
        self.n += 1
        self.sum_x += f.x or 0.0
        self.sum_y += f.y or 0.0
        self.sum_hazard += f.hazard or 0.0
        self.sum_quality += quality
        self.max_significance = max(self.max_significance, significance)

    def mode(self, name: str) -> Optional[str]:
        d = self.counts.get(name)
        if not d:
            return None
        return sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]

    def prototype(self) -> EpisodeFeatures:
        n = max(self.n, 1)
        return EpisodeFeatures(
            goal=self.mode("goal"), skill=self.mode("skill"), event_type=self.mode("event_type"),
            target=self.mode("target"), outcome=self.mode("outcome"), landmark=self.mode("landmark"),
            x=self.sum_x / n, y=self.sum_y / n, hazard=self.sum_hazard / n,
        )

    @property
    def mean_quality(self) -> float:
        return self.sum_quality / self.n if self.n else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"counts": self.counts, "n": self.n, "sum_x": self.sum_x, "sum_y": self.sum_y,
                "sum_hazard": self.sum_hazard, "sum_quality": self.sum_quality,
                "max_significance": self.max_significance}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GroupAgg":
        return cls(counts=d.get("counts", {}), n=d.get("n", 0), sum_x=d.get("sum_x", 0.0),
                   sum_y=d.get("sum_y", 0.0), sum_hazard=d.get("sum_hazard", 0.0),
                   sum_quality=d.get("sum_quality", 0.0),
                   max_significance=d.get("max_significance", 0.0))


@dataclass
class HierarchyNode:
    node_id: str
    level: str                                   # "bout" | "schema"
    episode_ids: List[int] = field(default_factory=list)
    start_tick: int = 0
    end_tick: int = 0
    agg: GroupAgg = field(default_factory=GroupAgg)
    closed: bool = False                         # closed bouts are immutable
    exemplar_id: Optional[int] = None
    exemplar_score: float = -1.0
    _proto: Optional[EpisodeFeatures] = field(default=None, repr=False, compare=False)

    def add(self, row: Dict[str, Any], feat: EpisodeFeatures) -> None:
        start, end = row.get("start_tick", 0), row.get("end_tick", 0)
        if not self.episode_ids:
            self.start_tick, self.end_tick = start, end
        else:
            self.start_tick, self.end_tick = min(self.start_tick, start), max(self.end_tick, end)
        self.episode_ids.append(row["id"])
        quality = row.get("overall_quality", 1.0)
        significance = row.get("peak_significance", 0.0)
        self.agg.add(feat, quality, significance)
        score = quality * significance
        if score > self.exemplar_score:
            self.exemplar_id, self.exemplar_score = row["id"], score
        self._proto = None

    @property
    def prototype(self) -> EpisodeFeatures:
        if self._proto is None:
            self._proto = self.agg.prototype()
        return self._proto

    def to_dict(self) -> Dict[str, Any]:
        return {"node_id": self.node_id, "level": self.level, "episode_ids": self.episode_ids,
                "start_tick": self.start_tick, "end_tick": self.end_tick,
                "agg": self.agg.to_dict(), "closed": self.closed,
                "exemplar_id": self.exemplar_id, "exemplar_score": self.exemplar_score}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "HierarchyNode":
        return cls(node_id=d["node_id"], level=d.get("level", "bout"),
                   episode_ids=list(d.get("episode_ids", [])),
                   start_tick=d.get("start_tick", 0), end_tick=d.get("end_tick", 0),
                   agg=GroupAgg.from_dict(d.get("agg", {})), closed=d.get("closed", False),
                   exemplar_id=d.get("exemplar_id"), exemplar_score=d.get("exemplar_score", -1.0))


STATE_VERSION = 1


@dataclass
class HierarchyState:
    run_id: str = ""
    watermark: int = 0                  # highest episode id already grouped
    next_bout: int = 1
    next_schema: int = 1
    open_bout: Optional[str] = None
    bouts: Dict[str, HierarchyNode] = field(default_factory=dict)
    schemas: Dict[str, HierarchyNode] = field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        return {"run_id": self.run_id, "watermark": self.watermark,
                "bouts": len(self.bouts), "schemas": len(self.schemas),
                "open_bout": self.open_bout,
                "episodes_grouped": sum(len(b.episode_ids) for b in self.bouts.values())}

    def to_dict(self) -> Dict[str, Any]:
        return {"version": STATE_VERSION, "run_id": self.run_id, "watermark": self.watermark,
                "next_bout": self.next_bout, "next_schema": self.next_schema,
                "open_bout": self.open_bout,
                "bouts": {k: v.to_dict() for k, v in self.bouts.items()},
                "schemas": {k: v.to_dict() for k, v in self.schemas.items()}}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "HierarchyState":
        return cls(run_id=d.get("run_id", ""), watermark=d.get("watermark", 0),
                   next_bout=d.get("next_bout", 1), next_schema=d.get("next_schema", 1),
                   open_bout=d.get("open_bout"),
                   bouts={k: HierarchyNode.from_dict(v) for k, v in d.get("bouts", {}).items()},
                   schemas={k: HierarchyNode.from_dict(v) for k, v in d.get("schemas", {}).items()})

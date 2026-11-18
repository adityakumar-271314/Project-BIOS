"""
HierarchyEngine: owns the hierarchy state of ONE run and keeps it in sync with the index.

Role: glue between the metadata index (source of rows), the builder (logic) and the store
(persistence). It never decides WHEN to run (consolidation does) and never loads payloads.
The hierarchy is a derived view: catch_up() repairs it after a crash and rebuild() recreates
it from scratch, always producing the same result.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from ..storage.metadata_index import MetadataIndex
from .grouper import GrouperConfig, HierarchyBuilder
from .nodes import HierarchyState
from .similarity import SimilarityEngine
from .store import HierarchyStore

FILENAME = "hierarchy.json"


class HierarchyEngine:
    def __init__(
        self,
        root: Path | str,
        run_id: str,
        config: Optional[GrouperConfig] = None,
        episode_sim: Optional[SimilarityEngine] = None,
        bout_sim: Optional[SimilarityEngine] = None,
    ):
        self.run_id = run_id
        self.store = HierarchyStore(Path(root) / FILENAME)
        self.builder = HierarchyBuilder(config, episode_sim, bout_sim)
        self.state: HierarchyState = self.store.load() or HierarchyState(run_id=run_id)
        self.dirty = False

    @property
    def episode_sim(self) -> SimilarityEngine:
        return self.builder.episode_sim

    def update(self, rows: Iterable[Dict[str, Any]]) -> int:
        applied = 0
        for row in sorted(rows, key=lambda r: r["id"]):
            if self.builder.add(self.state, row):
                applied += 1
        if applied:
            self.dirty = True
        return applied

    def catch_up(self, index: MetadataIndex) -> int:
        """Group every indexed episode newer than the watermark."""
        return self.update(index.rows_after(self.state.watermark))

    def rebuild(self, index: MetadataIndex) -> int:
        self.state = HierarchyState(run_id=self.run_id)
        self.dirty = True
        return self.update(index.rows)

    def save(self) -> bool:
        if not self.dirty:
            return False
        self.store.save(self.state)
        self.dirty = False
        return True

    def summary(self) -> Dict[str, Any]:
        return self.state.summary()

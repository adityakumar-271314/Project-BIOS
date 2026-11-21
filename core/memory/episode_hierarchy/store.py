"""Persistence of HierarchyState (hierarchy.json inside the run folder). Nothing else."""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

from ..storage.atomic_io import atomic_write_json, read_json
from .nodes import HierarchyState


class HierarchyStore:
    def __init__(self, path: Path | str):
        self.path = Path(path)

    def load(self) -> Optional[HierarchyState]:
        if not self.path.exists():
            return None
        data = read_json(self.path)
        try:
            if isinstance(data, dict):
                return HierarchyState.from_dict(data)
        except (KeyError, TypeError, ValueError):
            pass
        # The hierarchy is a derived view: set the unreadable file aside and let the
        # engine rebuild it from the metadata index.
        os.replace(self.path, self.path.with_name(self.path.name + ".corrupt"))
        return None

    def save(self, state: HierarchyState) -> None:
        atomic_write_json(self.path, state.to_dict())

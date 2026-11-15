from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any
from ..schemas import HierarchyGraphState

class HierarchyIndex:
    """
    Manages loading, saving, and persistence of the multi-tier hierarchy graph state
    stored in hierarchy_index.json within the run history directory.
    """
    def __init__(self, index_path: Path | str):
        self.path = Path(index_path)
        self.graph_state = HierarchyGraphState()
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.graph_state = HierarchyGraphState.from_dict(data)
            except Exception as e:
                print(f"[HierarchyIndex] Error loading hierarchy index from {self.path}: {e}")
                self.graph_state = HierarchyGraphState()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.graph_state.to_dict(), f, separators=(",", ":"))

    def update_from_state(self, graph_state: HierarchyGraphState) -> None:
        self.graph_state = graph_state
        self.save()
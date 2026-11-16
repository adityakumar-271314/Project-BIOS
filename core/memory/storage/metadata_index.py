import json
from pathlib import Path


class MetadataIndex:
    """
    Manages the unified memory index file containing both episode metadata descriptors 
    and cached high-level hierarchy groupings[cite: 1].
    """
    def __init__(self, index_path: Path | str):
        self.path = Path(index_path)
        self.data = {
            "version": 2,
            "episodes": [],
            "hierarchies": {}
        }
        self.load()

    def load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        self.data.update(loaded)
            except Exception as e:
                print(f"[MetadataIndex] Error loading index from {self.path}: {e}")

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, separators=(",", ":"))

    def add(self, meta: dict):
        self.data["episodes"].append(meta)
        self.save()

    def update_hierarchies(self, hierarchies_dict: dict):
        self.data["hierarchies"] = hierarchies_dict
        self.save()

    def query_latest(self):
        episodes = self.data.get("episodes", [])
        return episodes[-1] if episodes else None

    def query_recent(self, limit: int):
        episodes = self.data.get("episodes", [])
        return episodes[-limit:] if episodes else []

    def query_by_type(self, event_type: str, limit: int | None = None):
        episodes = self.data.get("episodes", [])
        matches = [e for e in episodes if e["event_type"] == event_type]
        return matches[-limit:] if limit else matches
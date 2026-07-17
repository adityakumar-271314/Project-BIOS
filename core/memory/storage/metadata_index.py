import json
from pathlib import Path

class MetadataIndex:
    def __init__(self, index_path: Path | str):
        self.path = Path(index_path)
        self.data = {"episodes": []}
        self.load()

    def load(self):
        if self.path.exists():
            with open(self.path, "r") as f:
                self.data = json.load(f)

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=4)

    def add(self, meta: dict):
        self.data["episodes"].append(meta)
        self.save()

    def query_latest(self):
        return self.data["episodes"][-1] if self.data["episodes"] else None

    def query_recent(self, limit: int):
        return self.data["episodes"][-limit:]

    def query_by_type(self, event_type: str, limit: int | None = None):
        matches = [e for e in self.data["episodes"] if e["event_type"] == event_type]
        return matches[-limit:] if limit else matches
"""
Per-run metadata index: one lean row per episode, append-only JSONL.

Role: hold and query EpisodeMeta rows in memory (by id, by time, by position) and persist
them crash-safely. It does NOT build hierarchy and does NOT load episode payloads.

File layout (runXXXX/episodes/memory_index.jsonl):
    line 1  : {"_header":true,"version":3,"run_id":"run0003"}
    line 2+ : one EpisodeMeta dict per line (append = O(1), a crash loses at most one line)
"""
from __future__ import annotations
import bisect
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .atomic_io import atomic_write_text, read_json

INDEX_VERSION = 3


def derive_run_id(root: Path) -> str:
    """runXXXX/episodes -> 'runXXXX'; any other folder -> its own name."""
    root = Path(root).resolve()
    return root.parent.name if root.name == "episodes" else root.name


class MetadataIndex:
    def __init__(self, root: Path | str, run_id: Optional[str] = None, cell_size: float = 100.0):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "memory_index.jsonl"
        self.legacy_path = self.root / "memory_index.json"
        self.run_id = run_id or derive_run_id(self.root)
        self.cell_size = cell_size

        self.rows: List[Dict[str, Any]] = []          # sorted by id
        self._ids: List[int] = []                     # parallel to rows
        self.by_id: Dict[int, Dict[str, Any]] = {}
        self._starts: List[Tuple[int, int]] = []      # (start_tick, id), sorted
        self._cells: Dict[Tuple[int, int], List[int]] = {}
        self.max_duration = 0
        self.max_significance = 0.0
        self.latest_tick = 0
        self.corrupt_lines = 0
        self.load()

    # ---------- persistence ----------
    def _header(self) -> str:
        return json.dumps({"_header": True, "version": INDEX_VERSION, "run_id": self.run_id},
                          separators=(",", ":"))

    def load(self) -> None:
        if self.path.exists():
            self._read_jsonl()
        elif self.legacy_path.exists():
            self._migrate_legacy()
        else:
            atomic_write_text(self.path, self._header() + "\n")

    def _read_jsonl(self) -> None:
        with open(self.path, "r", encoding="utf-8") as f:
            text = f.read()
        header_run = None
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                self.corrupt_lines += 1
                continue
            if not isinstance(obj, dict):
                self.corrupt_lines += 1
            elif obj.get("_header"):
                header_run = obj.get("run_id")
            elif "id" in obj:
                self._index_row(obj)
        if header_run:
            self.run_id = header_run
        # A torn final line (crash mid-append) or garbage lines: compact the file so the
        # next append starts on a clean line. Orphaned episodes are re-added by the archive.
        if self.corrupt_lines or (text and not text.endswith("\n")):
            self._rewrite()

    def _migrate_legacy(self) -> None:
        data = read_json(self.legacy_path, {}) or {}
        for row in data.get("episodes", []):
            if isinstance(row, dict) and "id" in row:
                row = {k: v for k, v in row.items() if k != "node_id"}
                self._index_row(row)
        self._rewrite()
        os.replace(self.legacy_path, self.legacy_path.with_name("memory_index.json.legacy.bak"))

    def _rewrite(self) -> None:
        lines = [self._header()] + [json.dumps(r, separators=(",", ":")) for r in self.rows]
        atomic_write_text(self.path, "\n".join(lines) + "\n")

    def reset(self) -> None:
        self.rows, self._ids, self.by_id = [], [], {}
        self._starts, self._cells = [], {}
        self.max_duration, self.max_significance, self.latest_tick = 0, 0.0, 0
        self.corrupt_lines = 0
        self._rewrite()

    # ---------- write ----------
    def add(self, meta: Dict[str, Any]) -> bool:
        if "id" not in meta:
            raise ValueError("metadata row needs an 'id'")
        if meta["id"] in self.by_id:
            return False
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(meta, separators=(",", ":")) + "\n")
            f.flush()
        self._index_row(meta)
        return True

    def _index_row(self, row: Dict[str, Any]) -> None:
        eid = row["id"]
        if eid in self.by_id:
            return
        if not self._ids or eid > self._ids[-1]:
            self._ids.append(eid)
            self.rows.append(row)
        else:
            i = bisect.bisect_left(self._ids, eid)
            self._ids.insert(i, eid)
            self.rows.insert(i, row)
        self.by_id[eid] = row
        start, end = row.get("start_tick", 0), row.get("end_tick", 0)
        bisect.insort(self._starts, (start, eid))
        self.max_duration = max(self.max_duration, end - start)
        self.max_significance = max(self.max_significance, row.get("peak_significance", 0.0))
        self.latest_tick = max(self.latest_tick, end)
        cell = self._cell(row.get("peak_x", 0.0), row.get("peak_y", 0.0))
        self._cells.setdefault(cell, []).append(eid)

    def _cell(self, x: float, y: float) -> Tuple[int, int]:
        return (math.floor(x / self.cell_size), math.floor(y / self.cell_size))

    # ---------- read ----------
    def __len__(self) -> int:
        return len(self.rows)

    def get(self, episode_id: int) -> Optional[Dict[str, Any]]:
        return self.by_id.get(episode_id)

    def rows_after(self, episode_id: int) -> List[Dict[str, Any]]:
        return self.rows[bisect.bisect_right(self._ids, episode_id):]

    def overlapping(self, t0: int, t1: int) -> List[Dict[str, Any]]:
        """Rows whose [start_tick, end_tick] intersects [t0, t1]."""
        hi = bisect.bisect_right(self._starts, (t1, float("inf")))
        out = []
        for j in range(hi - 1, -1, -1):
            start, eid = self._starts[j]
            if start < t0 - self.max_duration:
                break
            row = self.by_id[eid]
            if row.get("end_tick", 0) >= t0:
                out.append(row)
        return out

    def near(self, x: float, y: float, radius: float) -> List[Dict[str, Any]]:
        cx0, cy0 = self._cell(x - radius, y - radius)
        cx1, cy1 = self._cell(x + radius, y + radius)
        if (cx1 - cx0 + 1) * (cy1 - cy0 + 1) > max(len(self.rows), 1):
            candidates = self.rows
        else:
            candidates = [self.by_id[i] for cx in range(cx0, cx1 + 1)
                          for cy in range(cy0, cy1 + 1) for i in self._cells.get((cx, cy), ())]
        hit = [r for r in candidates
               if math.hypot(r.get("peak_x", 0.0) - x, r.get("peak_y", 0.0) - y) <= radius]
        return sorted(hit, key=lambda r: r["id"])

    def query_latest(self) -> Optional[Dict[str, Any]]:
        return self.rows[-1] if self.rows else None

    def query_recent(self, limit: int) -> List[Dict[str, Any]]:
        return self.rows[-limit:] if self.rows else []

    def query_by_type(self, event_type: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        matches = [r for r in self.rows if r.get("event_type") == event_type]
        return matches[-limit:] if limit else matches

    @property
    def data(self) -> Dict[str, Any]:
        """Read-only compatibility view of the old {'episodes': [...]} shape."""
        return {"version": INDEX_VERSION, "run_id": self.run_id, "episodes": self.rows}

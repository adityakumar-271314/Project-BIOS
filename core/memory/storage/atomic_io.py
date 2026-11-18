"""Crash-safe file helpers: write to a temp file, fsync, then atomically replace."""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any


def atomic_write_text(path: Path | str, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_write_json(path: Path | str, obj: Any) -> None:
    atomic_write_text(path, json.dumps(obj, separators=(",", ":")))


def read_json(path: Path | str, default: Any = None) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default

"""
Compact on-disk layout for episode.json (format 3).

Only concern: size. key_frames are stored column-wise (field names appear once, not once
per frame), ticks are delta-encoded, spatial context is stored as short arrays, and floats
are rounded. unpack() restores exactly the dict shape EpisodicEvent.from_dict expects, and
payloads without the "kf" key (old format) pass through untouched.
"""

from __future__ import annotations
from typing import Any, Dict, Optional

FORMAT_VERSION = 3


def _round(obj: Any, digits: Optional[int]) -> Any:
    if digits is None:
        return obj
    if isinstance(obj, float):
        return round(obj, digits)
    if isinstance(obj, dict):
        return {k: _round(v, digits) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_round(v, digits) for v in obj]
    return obj


def _enum(v: Any) -> Any:
    return getattr(v, "value", v)


def pack(payload: Dict[str, Any], digits: Optional[int] = 4) -> Dict[str, Any]:
    out = {k: v for k, v in payload.items() if k != "key_frames"}
    frames = payload.get("key_frames") or []
    if frames:
        keys = [k for k in frames[0] if k != "spatial_context"]
        cols = {k: [f.get(k) for f in frames] for k in keys}
        kf: Dict[str, Any] = {"cols": cols}
        ticks = cols.get("tick")
        if ticks and all(isinstance(t, int) for t in ticks):
            cols["tick"] = [ticks[0]] + [b - a for a, b in zip(ticks, ticks[1:])]
            kf["dt"] = 1
        sc = [
            [
                [
                    _enum(s.get("entity_type")),
                    s.get("pos_x"),
                    s.get("pos_y"),
                    s.get("entity_id"),
                    s.get("intensity"),
                ]
                for s in f.get("spatial_context", [])
            ]
            for f in frames
        ]
        if any(sc):
            kf["sc"] = sc
        out["kf"] = kf
    out["fmt"] = FORMAT_VERSION
    return _round(out, digits)


def unpack(data: Dict[str, Any]) -> Dict[str, Any]:
    kf = data.get("kf")
    if kf is None:
        return data
    cols = kf.get("cols", {})
    n = len(next(iter(cols.values()))) if cols else 0
    if kf.get("dt") and "tick" in cols:
        acc, ticks = 0, []
        for i, d in enumerate(cols["tick"]):
            acc = d if i == 0 else acc + d
            ticks.append(acc)
        cols = dict(cols, tick=ticks)
    sc = kf.get("sc")
    frames = []
    for i in range(n):
        f = {k: v[i] for k, v in cols.items()}
        f["spatial_context"] = (
            [
                {
                    "entity_type": e[0],
                    "pos_x": e[1],
                    "pos_y": e[2],
                    "entity_id": e[3],
                    "intensity": e[4],
                }
                for e in sc[i]
            ]
            if sc
            else []
        )
        frames.append(f)
    out = {k: v for k, v in data.items() if k not in ("kf", "fmt")}
    out["key_frames"] = frames
    return out

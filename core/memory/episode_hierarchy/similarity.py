"""
Similarity engine: the ONLY place that decides how alike two episodes (or an episode and a
group prototype, or a query and an episode) are. Pure functions, no I/O, no ML.

Everything else (bout building, schema building, retrieval) calls this, so tuning
"what counts as similar" is a weights/threshold change in one file.

score() in [0,1] = weighted agreement over the dimensions known on BOTH sides, with:
  * veto fields: a known mismatch (default: goal) forces 0, so a 'forage' episode can never
    look similar to a 'flee' one however close in space;
  * missing-data handling: unknown dimensions are skipped, not counted as matches (so
    None == None is NOT a match), and sparse comparisons are discounted.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Tuple

CATEGORICAL = ("goal", "skill", "event_type", "target", "outcome", "landmark")

# Same-kind episodes recurring over time (schemas, retrieval)
EPISODE_WEIGHTS: Dict[str, float] = {
    "goal": 0.25, "skill": 0.15, "event_type": 0.10, "target": 0.05,
    "outcome": 0.10, "landmark": 0.15, "space": 0.15, "hazard": 0.05,
}
# Consecutive episodes belonging to the same activity (bouts): outcome/event type may change
BOUT_WEIGHTS: Dict[str, float] = {
    "goal": 0.45, "skill": 0.20, "landmark": 0.20, "space": 0.15,
}


def _s(v: Any) -> Optional[str]:
    return None if v is None or v == "" else str(v)


@dataclass(slots=True, frozen=True)
class EpisodeFeatures:
    goal: Optional[str] = None
    skill: Optional[str] = None
    event_type: Optional[str] = None
    target: Optional[str] = None
    outcome: Optional[str] = None
    landmark: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    hazard: Optional[float] = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "EpisodeFeatures":
        outcome = _s(row.get("outcome_status"))
        return cls(
            goal=_s(row.get("dominant_goal")),
            skill=_s(row.get("dominant_skill")),
            event_type=_s(row.get("event_type")),
            target=_s(row.get("dominant_target")),
            outcome=None if outcome == "unknown" else outcome,
            landmark=_s(row.get("nearest_landmark_id")),
            x=row.get("peak_x"),
            y=row.get("peak_y"),
            hazard=row.get("max_hazard_exposure"),
        )


class SimilarityEngine:
    def __init__(
        self,
        weights: Optional[Mapping[str, float]] = None,
        spatial_scale: float = 150.0,
        veto: Tuple[str, ...] = ("goal",),
    ):
        self.w = dict(weights or EPISODE_WEIGHTS)
        self.total = sum(self.w.values()) or 1.0
        self.spatial_scale = spatial_scale
        self.veto = veto

    def vetoed(self, a: EpisodeFeatures, b: EpisodeFeatures) -> bool:
        for name in self.veto:
            va, vb = getattr(a, name), getattr(b, name)
            if va is not None and vb is not None and va != vb:
                return True
        return False

    def score(self, a: EpisodeFeatures, b: EpisodeFeatures, penalize_missing: bool = True) -> float:
        if self.vetoed(a, b):
            return 0.0
        num = den = 0.0
        for name in CATEGORICAL:
            w = self.w.get(name, 0.0)
            if not w:
                continue
            va, vb = getattr(a, name), getattr(b, name)
            if va is None or vb is None:
                continue
            den += w
            num += w if va == vb else 0.0
        w = self.w.get("space", 0.0)
        if w and None not in (a.x, a.y, b.x, b.y):
            den += w
            num += w * math.exp(-math.hypot(a.x - b.x, a.y - b.y) / self.spatial_scale)
        w = self.w.get("hazard", 0.0)
        if w and a.hazard is not None and b.hazard is not None:
            den += w
            num += w * (1.0 - min(1.0, abs(a.hazard - b.hazard)))
        if den <= 0.0:
            return 0.0
        base = num / den
        if penalize_missing:
            base *= 0.5 + 0.5 * (den / self.total)
        return base

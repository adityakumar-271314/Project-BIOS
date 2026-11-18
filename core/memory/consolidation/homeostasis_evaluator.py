"""
HomeostasisEvaluator: answers ONE question - "is the agent calm enough to spend compute on
housekeeping right now?" It never groups anything and never touches storage.

Changes vs the point-sample version:
  * is_safe_window() looks at the last N frames (smoothed), not a single frame;
  * an optional external veto (set_veto) is the hook for a future brain/sleep controller:
    it can only FORBID consolidation, it cannot be asked to predict future ticks;
  * starvation is not handled here: the scheduler (DeferredGrouper) has a hard deadline.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Sequence


@dataclass(slots=True)
class HomeostasisConfig:
    """Thresholds governing when an agent is under high compute/survival demand."""
    max_safe_stress: float = 0.4
    max_safe_fear: float = 0.3
    max_safe_hazard_stim: float = 0.2
    min_safe_integrity: float = 0.5
    max_safe_prediction_error: float = 0.5
    calm_frames: int = 30              # how many most-recent frames are inspected
    max_demand_fraction: float = 0.0   # tolerated share of demanding frames in that window


class HomeostasisEvaluator:
    def __init__(self, config: Optional[HomeostasisConfig] = None):
        self.config = config or HomeostasisConfig()
        self._veto: Optional[Callable[[], bool]] = None

    def set_veto(self, veto: Optional[Callable[[], bool]]) -> None:
        """veto() -> True means 'do not consolidate now' (e.g. brain is busy)."""
        self._veto = veto

    def evaluate_demand(self, current_snapshot: Any, recent_prediction_error: float = 0.0) -> Dict[str, Any]:
        if hasattr(current_snapshot, "stress"):
            stress = current_snapshot.stress
            fear = current_snapshot.fear
            hazard_stim = current_snapshot.hazard_stim
            integrity = current_snapshot.integrity
        elif isinstance(current_snapshot, dict):
            stress = current_snapshot.get("stress", 0.0)
            fear = current_snapshot.get("fear", 0.0)
            hazard_stim = current_snapshot.get("hazard_stim", 0.0)
            integrity = current_snapshot.get("integrity", 1.0)
        else:
            return {"is_high_demand": True, "reasons": ["invalid_snapshot_format"]}

        c = self.config
        reasons = []
        if stress > c.max_safe_stress:
            reasons.append(f"high_stress ({stress:.2f})")
        if fear > c.max_safe_fear:
            reasons.append(f"high_fear ({fear:.2f})")
        if hazard_stim > c.max_safe_hazard_stim:
            reasons.append(f"hazard_exposure ({hazard_stim:.2f})")
        if integrity < c.min_safe_integrity:
            reasons.append(f"low_integrity ({integrity:.2f})")
        if recent_prediction_error > c.max_safe_prediction_error:
            reasons.append(f"high_prediction_error ({recent_prediction_error:.2f})")
        return {
            "is_high_demand": bool(reasons),
            "reasons": reasons,
            "metrics": {"stress": stress, "fear": fear, "hazard_stim": hazard_stim,
                        "integrity": integrity, "prediction_error": recent_prediction_error},
        }

    def is_safe_for_consolidation(self, current_snapshot: Any, recent_prediction_error: float = 0.0) -> bool:
        """Single-sample check (kept for compatibility)."""
        if self._veto is not None and self._veto():
            return False
        return not self.evaluate_demand(current_snapshot, recent_prediction_error)["is_high_demand"]

    def is_safe_window(self, frames: Sequence[Any]) -> bool:
        """Smoothed check over the most recent frames (objects with .snapshot/.prediction_error)."""
        if self._veto is not None and self._veto():
            return False
        tail = list(frames)[-max(1, self.config.calm_frames):]
        if not tail:
            return False
        demanding = sum(
            1 for fr in tail
            if self.evaluate_demand(fr.snapshot, getattr(fr, "prediction_error", 0.0))["is_high_demand"]
        )
        return demanding / len(tail) <= self.config.max_demand_fraction

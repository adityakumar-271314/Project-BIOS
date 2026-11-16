from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass(slots=True)
class HomeostasisConfig:
    """Thresholds governing when an agent is under high compute/survival demand."""
    max_safe_stress: float = 0.4
    max_safe_fear: float = 0.3
    max_safe_hazard_stim: float = 0.2
    min_safe_integrity: float = 0.5
    max_safe_prediction_error: float = 0.5


class HomeostasisEvaluator:
    """
    Evaluates current bodily vitals and environmental telemetry to determine 
    if the agent is experiencing high survival pressure or cognitive load.
    """
    def __init__(self, config: Optional[HomeostasisConfig] = None):
        self.config = config or HomeostasisConfig()

    def evaluate_demand(self, current_snapshot: Any, recent_prediction_error: float = 0.0) -> Dict[str, Any]:
        """
        Inspects vitals and stimuli from a tick snapshot or state dictionary 
        to quantify current compute demand.
        """
        # Handle both object attributes (TickSnapshot) or dictionaries
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

        reasons = []
        
        if stress > self.config.max_safe_stress:
            reasons.append(f"high_stress ({stress:.2f})")
        if fear > self.config.max_safe_fear:
            reasons.append(f"high_fear ({fear:.2f})")
        if hazard_stim > self.config.max_safe_hazard_stim:
            reasons.append(f"hazard_exposure ({hazard_stim:.2f})")
        if integrity < self.config.min_safe_integrity:
            reasons.append(f"low_integrity ({integrity:.2f})")
        if recent_prediction_error > self.config.max_safe_prediction_error:
            reasons.append(f"high_prediction_error ({recent_prediction_error:.2f})")

        is_high_demand = len(reasons) > 0

        return {
            "is_high_demand": is_high_demand,
            "reasons": reasons,
            "metrics": {
                "stress": stress,
                "fear": fear,
                "hazard_stim": hazard_stim,
                "integrity": integrity,
                "prediction_error": recent_prediction_error
            }
        }

    def is_safe_for_consolidation(self, current_snapshot: Any, recent_prediction_error: float = 0.0) -> bool:
        """
        Returns True only when the agent's vitals are stable, safe, 
        and free from immediate survival pressure.
        """
        evaluation = self.evaluate_demand(current_snapshot, recent_prediction_error)
        return not evaluation["is_high_demand"]
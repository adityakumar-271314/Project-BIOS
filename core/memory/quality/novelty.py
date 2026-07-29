from typing import Tuple, List, Optional, Set
from ..schemas import EpisodicEvent


class NoveltyEvaluator:
    """
    Evaluates episode novelty based on rare signature configurations,
    unusual behavioral drivers, and non-standard outcomes.
    """

    def __init__(self, common_drivers_baseline: Optional[Set[str]] = None):
        self.common_drivers_baseline = common_drivers_baseline or {
            "reward_acquisition",
            "behavioral_shift",
        }

    def evaluate(
        self,
        event: EpisodicEvent,
        history: Optional[List[EpisodicEvent]] = None,
    ) -> Tuple[float, List[str]]:
        reasons = []
        sig = event.signature

        # 1. Driver-based Novelty
        drivers = set(sig.primary_importance_drivers)
        rare_drivers = drivers - self.common_drivers_baseline
        driver_novelty = min(1.0, len(rare_drivers) * 0.35)

        if "integrity_change" in rare_drivers or "hazard_exposure" in rare_drivers:
            reasons.append("high_impact_driver_present")

        # 2. Behavioral Complexity & Transition Novelty
        complexity_novelty = min(1.0, sig.behavioral_complexity * 2.0)

        # 3. Overall Batch/History Novelty Comparison
        history_novelty = 0.5
        if history:
            unique_goals = {
                e.signature.dominant_goal for e in history if e.signature.dominant_goal
            }
            if sig.dominant_goal and sig.dominant_goal not in unique_goals:
                history_novelty += 0.4
                reasons.append("unseen_dominant_goal")

        # Composite Novelty Score
        novelty = (
            (0.4 * driver_novelty)
            + (0.3 * complexity_novelty)
            + (0.3 * history_novelty)
        )

        # Blend with event's internal overall novelty metric if present
        if sig.overall_novelty > 0:
            novelty = 0.6 * novelty + 0.4 * sig.overall_novelty

        return round(min(1.0, max(0.0, novelty)), 4), reasons

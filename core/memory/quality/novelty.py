from typing import Tuple, List, Optional, Set
from ..schemas import EpisodicEvent


class NoveltyEvaluator:
    """
    Evaluates episode novelty based on rare signature configurations,
    unusual behavioral drivers, and non-standard outcome statuses.
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

        drivers = set(sig.primary_importance_drivers)
        rare_drivers = drivers - self.common_drivers_baseline
        driver_novelty = min(1.0, len(rare_drivers) * 0.35)

        if "integrity_change" in rare_drivers or "hazard_exposure" in rare_drivers:
            reasons.append("high_impact_driver_present")

        macro_novelty = min(1.0, len(sig.macro_transitions) * 0.25)

        history_novelty = 0.5
        if history:
            unique_goals = {
                e.signature.dominant_goal for e in history if e.signature.dominant_goal
            }
            if sig.dominant_goal and sig.dominant_goal not in unique_goals:
                history_novelty += 0.4
                reasons.append("unseen_dominant_goal")

        novelty = (
            (0.4 * driver_novelty) + (0.3 * macro_novelty) + (0.3 * history_novelty)
        )

        return round(min(1.0, max(0.0, novelty)), 4), reasons

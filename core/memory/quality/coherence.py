import math
from typing import Tuple, List
from ..schemas import EpisodicEvent


class CoherenceEvaluator:
    """
    Evaluates how behaviorally unified and continuous an episode is using compressed macro-transitions.
    """

    def __init__(
        self,
        max_allowed_transition_rate: float = 0.05,
        oscillation_penalty_weight: float = 0.4,
    ):
        self.max_allowed_transition_rate = max_allowed_transition_rate
        self.oscillation_penalty_weight = oscillation_penalty_weight

    def evaluate(self, event: EpisodicEvent) -> Tuple[float, List[str]]:
        reasons = []
        sig = event.signature
        duration = max(1, sig.duration_ticks)

        total_macro_transitions = len(sig.macro_transitions)

        # 1. Macro-Transition Density Penalty
        transition_rate = total_macro_transitions / duration
        if transition_rate > self.max_allowed_transition_rate:
            reasons.append("high_macro_transition_density")

        density_score = math.exp(
            -2.0 * max(0.0, transition_rate - self.max_allowed_transition_rate)
        )

        # 2. Oscillation Detection across macro transitions
        oscillation_count = self._count_oscillations(
            [t.to_state for t in sig.macro_transitions if t.to_state]
        )

        oscillation_penalty = 0.0
        if oscillation_count > 0:
            reasons.append(f"state_oscillation_detected_{oscillation_count}")
            oscillation_penalty = min(
                1.0, oscillation_count * self.oscillation_penalty_weight
            )

        coherence = max(0.0, density_score * (1.0 - oscillation_penalty))

        # Composite identity check
        if not sig.dominant_goal and not sig.dominant_skill:
            coherence *= 0.8
            reasons.append("missing_dominant_behavior")

        return round(coherence, 4), reasons

    def _count_oscillations(self, states: List[str]) -> int:
        if len(states) < 3:
            return 0
        oscillations = 0
        for i in range(len(states) - 2):
            if states[i] == states[i + 2] and states[i] != states[i + 1]:
                oscillations += 1
        return oscillations

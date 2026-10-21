from typing import Dict, List, Tuple
from ..schemas import EpisodeFrame


class BoundaryScore:
    """
    Combines rule activations and continuous frame metrics to calculate normalized
    confidence scores (0.0 to 1.0) and consolidated evidence lists for boundary candidates.
    """

    def __init__(
        self,
        rule_weight: float = 0.6,
        metric_weight: float = 0.4,
    ):
        """
        Args:
            rule_weight: Weight given to discrete rule triggers.
            metric_weight: Weight given to continuous metrics (importance, surprise, attention).
        """
        self.rule_weight = rule_weight
        self.metric_weight = metric_weight

    def score_frame(
        self,
        prev_frame: EpisodeFrame,
        curr_frame: EpisodeFrame,
        start_triggers: Dict[str, float],
        end_triggers: Dict[str, float],
    ) -> Tuple[float, List[str], float, List[str]]:
        """
        Computes start and end confidence scores along with reason descriptions.

        Returns:
            A tuple of:
            (start_confidence, start_reasons, end_confidence, end_reasons)
        """
        if not curr_frame:
            return 0.0, [], 0.0, []

        start_confidence, start_reasons = self._score_start(
            prev_frame=prev_frame,
            curr_frame=curr_frame,
            triggers=start_triggers,
        )

        end_confidence, end_reasons = self._score_end(
            prev_frame=prev_frame,
            curr_frame=curr_frame,
            triggers=end_triggers,
        )

        return start_confidence, start_reasons, end_confidence, end_reasons

    def _has_experiential_consequences(self, prev_frame: EpisodeFrame, curr_frame: EpisodeFrame) -> bool:
        """
        STEP 4: Verifies if a transition is accompanied by genuine experiential consequences
        (vitals delta, emotional spike, or environmental stimulus change) rather than empty churn.
        """
        if not prev_frame:
            return True

        # Check for significant vital changes
        vitals_changed = (
            abs(curr_frame.energy_delta) > 0.02 or
            abs(curr_frame.integrity_delta) > 0.01 or
            abs(curr_frame.stress_delta) > 0.05 or
            abs(curr_frame.fear_delta) > 0.05
        )

        # Check for environmental stimuli changes or novelty/prediction error spikes
        env_changed = (
            curr_frame.snapshot.hazard_stim > 0.1 or
            curr_frame.snapshot.food_stim > 0.1 or
            curr_frame.prediction_error > 1.0 or
            curr_frame.novelty > 0.3
        )

        return vitals_changed or env_changed

    def _score_start(
        self,
        prev_frame: EpisodeFrame,
        curr_frame: EpisodeFrame,
        triggers: Dict[str, float],
    ) -> Tuple[float, List[str]]:
        # STEP 4: Enforce corroborating consequence gates for transition signals.
        # If strong continuity evidence exists (calm emotions, stable vitals, stable environment)
        # without verified experiential consequences, block transition/churn trigger flags entirely.
        has_consequences = self._has_experiential_consequences(prev_frame, curr_frame)
        
        filtered_triggers = {}
        for rule_name, score in triggers.items():
            is_transition_rule = any(term in rule_name for term in ["goal_changed", "skill_changed", "target_changed"])
            if is_transition_rule and not has_consequences:
                # Suppress transition triggers entirely if there are no corroborating consequences
                continue
            filtered_triggers[rule_name] = score

        triggers = filtered_triggers
        reasons: List[str] = list(triggers.keys())
        
        if not triggers and curr_frame.importance < 0.4:
            return 0.0, []

        # 1. Rule component: max trigger score
        rule_score = max(triggers.values()) if triggers else 0.0

        # 2. Continuous metrics component
        importance = curr_frame.importance
        attention = curr_frame.attention_score
        surprise_norm = min(1.0, curr_frame.prediction_error / 3.0)

        continuous_score = (
            (importance * 0.4) + (attention * 0.3) + (surprise_norm * 0.3)
        )

        if continuous_score > 0.6 and "high_metric_spike" not in reasons:
            reasons.append("high_metric_spike")

        # 3. Composite score calculation
        if triggers:
            raw_score = (rule_score * self.rule_weight) + (
                continuous_score * self.metric_weight
            )
        else:
            raw_score = continuous_score * 0.7

        confidence = max(0.0, min(1.0, raw_score))
        return confidence, reasons

    def _score_end(
        self,
        prev_frame: EpisodeFrame,
        curr_frame: EpisodeFrame,
        triggers: Dict[str, float],
    ) -> Tuple[float, List[str]]:
        has_consequences = self._has_experiential_consequences(prev_frame, curr_frame)
        
        filtered_triggers = {
            r: score for r, score in triggers.items()
            if not (any(term in r for term in ["goal_changed", "skill_changed", "target_changed"]) and not has_consequences)
        }
        triggers = filtered_triggers
        reasons: List[str] = list(triggers.keys())

        rule_score = max(triggers.values()) if triggers else 0.0

        attention_drop = 0.0
        if prev_frame:
            attention_drop = max(
                0.0, prev_frame.attention_score - curr_frame.attention_score
            )

        low_importance_bonus = (
            max(0.0, 0.5 - curr_frame.importance)
            if prev_frame and prev_frame.importance > 0.5
            else 0.0
        )

        continuous_score = (attention_drop * 0.6) + (low_importance_bonus * 0.4)

        if continuous_score > 0.5 and "metric_stabilization" not in reasons:
            reasons.append("metric_stabilization")

        if triggers:
            raw_score = (rule_score * self.rule_weight) + (
                continuous_score * self.metric_weight
            )
        else:
            raw_score = continuous_score * 0.6

        confidence = max(0.0, min(1.0, raw_score))
        return confidence, reasons
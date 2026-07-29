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

    def _score_start(
        self,
        prev_frame: EpisodeFrame,
        curr_frame: EpisodeFrame,
        triggers: Dict[str, float],
    ) -> Tuple[float, List[str]]:
        reasons: List[str] = list(triggers.keys())
        if not triggers and curr_frame.importance < 0.4:
            return 0.0, []

        # 1. Rule component: max trigger score
        rule_score = max(triggers.values()) if triggers else 0.0

        # 2. Continuous metrics component
        # Strong start indicators: high importance, high prediction error (surprise), or elevated attention score
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
            # Metric-only fallback if no discrete rules fired
            raw_score = continuous_score * 0.7

        # Bound to [0.0, 1.0]
        confidence = max(0.0, min(1.0, raw_score))
        return confidence, reasons

    def _score_end(
        self,
        prev_frame: EpisodeFrame,
        curr_frame: EpisodeFrame,
        triggers: Dict[str, float],
    ) -> Tuple[float, List[str]]:
        reasons: List[str] = list(triggers.keys())

        # 1. Rule component: max trigger score
        rule_score = max(triggers.values()) if triggers else 0.0

        # 2. Continuous metrics component
        # Strong end indicators: low relative importance/attention after an active state,
        # or settling emotional drives
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

        # 3. Composite score calculation
        if triggers:
            raw_score = (rule_score * self.rule_weight) + (
                continuous_score * self.metric_weight
            )
        else:
            raw_score = continuous_score * 0.6

        confidence = max(0.0, min(1.0, raw_score))
        return confidence, reasons

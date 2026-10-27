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
        self.rule_weight = rule_weight
        self.metric_weight = metric_weight

    def score_frame(
        self,
        recent_frames: List[EpisodeFrame],
        start_triggers: Dict[str, float],
        end_triggers: Dict[str, float],
    ) -> Tuple[float, List[str], float, List[str]]:
        if not recent_frames:
            return 0.0, [], 0.0, []

        curr_frame = recent_frames[-1]
        prev_frame = recent_frames[-2] if len(recent_frames) >= 2 else None

        start_confidence, start_reasons = self._score_start(
            recent_frames=recent_frames,
            triggers=start_triggers,
        )

        end_confidence, end_reasons = self._score_end(
            recent_frames=recent_frames,
            triggers=end_triggers,
        )

        return start_confidence, start_reasons, end_confidence, end_reasons

    def _has_experiential_consequences(self, recent_frames: List[EpisodeFrame]) -> bool:
        """
        Enforces multi-frame accumulation: verifies if a transition is accompanied 
        by sustained vital deviations or environmental changes across the recent window.
        """
        if len(recent_frames) < 2:
            return True

        # Compute cumulative or sustained deltas across the rolling window
        total_energy_delta = sum(abs(f.energy_delta) for f in recent_frames[1:])
        total_stress_delta = sum(f.stress_delta for f in recent_frames[1:])
        total_fear_delta = sum(f.fear_delta for f in recent_frames[1:])

        # Sustained threshold checks instead of single-frame spikes
        vitals_sustained = (
            total_energy_delta > 0.04 or
            total_stress_delta > 0.08 or
            total_fear_delta > 0.08
        )

        # Environmental or novelty persistence
        env_persistent = any(
            f.snapshot.hazard_stim > 0.15 or 
            f.snapshot.food_stim > 0.15 or 
            f.prediction_error > 1.2 or 
            f.novelty > 0.35
            for f in recent_frames
        )

        return vitals_sustained or env_persistent

    def _score_start(
        self,
        recent_frames: List[EpisodeFrame],
        triggers: Dict[str, float],
    ) -> Tuple[float, List[str]]:
        curr_frame = recent_frames[-1]
        has_consequences = self._has_experiential_consequences(recent_frames)
        
        filtered_triggers = {}
        for rule_name, score in triggers.items():
            is_transition_rule = any(term in rule_name for term in ["goal_changed", "skill_changed", "target_changed"])
            if is_transition_rule and not has_consequences:
                continue
            filtered_triggers[rule_name] = score

        triggers = filtered_triggers
        reasons: List[str] = list(triggers.keys())
        
        if not triggers and curr_frame.importance < 0.4:
            return 0.0, []

        rule_score = max(triggers.values()) if triggers else 0.0
        importance = curr_frame.importance
        attention = curr_frame.attention_score
        surprise_norm = min(1.0, curr_frame.prediction_error / 3.0)

        continuous_score = (
            (importance * 0.4) + (attention * 0.3) + (surprise_norm * 0.3)
        )

        if continuous_score > 0.6 and "high_metric_spike" not in reasons:
            reasons.append("high_metric_spike")

        raw_score = (
            (rule_score * self.rule_weight) + (continuous_score * self.metric_weight)
            if triggers
            else continuous_score * 0.7
        )

        return max(0.0, min(1.0, raw_score)), reasons

    def _score_end(
        self,
        recent_frames: List[EpisodeFrame],
        triggers: Dict[str, float],
    ) -> Tuple[float, List[str]]:
        curr_frame = recent_frames[-1]
        prev_frame = recent_frames[-2] if len(recent_frames) >= 2 else None
        
        has_consequences = self._has_experiential_consequences(recent_frames)
        
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

        raw_score = (
            (rule_score * self.rule_weight) + (continuous_score * self.metric_weight)
            if triggers
            else continuous_score * 0.6
        )

        return max(0.0, min(1.0, raw_score)), reasons
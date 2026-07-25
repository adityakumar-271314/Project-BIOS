from typing import Dict, Set
from ..schemas import TickSnapshot


class FrameMetrics:
    """Engine for continuous numerical metric scoring across emotional, surprising, and causal axes."""

    def compute(
        self,
        prev: TickSnapshot,
        curr: TickSnapshot,
        deltas: Dict[str, float],
        event_tags: Set[str],
        transition_flags: Dict[str, bool],
        stats: Dict[str, any],
        config: any = None,
    ) -> Dict[str, float]:
        if not prev or not curr:
            return {
                "importance": 0.0,
                "prediction_error": 0.0,
                "attention_score": 0.0,
                "novelty": 0.0,
            }

        min_samples = getattr(config, "episodic_min_samples", 10) if config else 10
        min_std = getattr(config, "min_std", 0.01) if config else 0.01

        # 1. Prediction Error (Statistical Surprise via Z-score)
        surprise_scores = []
        for key in ["energy_delta", "integrity_delta", "stress_delta", "fear_delta", "drive_delta"]:
            if key in stats and stats[key].n >= min_samples:
                s = stats[key]
                effective_std = max(s.std, min_std)
                z_score = abs(deltas.get(key, 0.0) - s.mean) / effective_std
                surprise_scores.append(z_score)

        prediction_error = (
            sum(surprise_scores) / len(surprise_scores) if surprise_scores else 0.0
        )

        # 2. Emotional Intensity & Novelty Proxy
        emotional_intensity = curr.stress * 0.3 + curr.fear * 0.5 + curr.drive * 0.2
        novelty = min(1.0, prediction_error * 0.2)

        # 3. Attention Score (Driven by environmental changes, active goal priorities, and threats)
        attention_score = (
            curr.hazard_stim * 0.4
            + curr.goal_priority * 0.3
            + (0.3 if "target_acquired" in event_tags else 0.0)
        )

        # 4. Composite Importance
        causal_boost = 0.0
        if any(transition_flags.values()):
            causal_boost += 0.2
        if "damage_taken" in event_tags or "entered_hazard" in event_tags:
            causal_boost += 0.3

        importance = (
            (prediction_error * 0.4)
            + (emotional_intensity * 0.3)
            + (attention_score * 0.1)
            + causal_boost
        )

        return {
            "importance": importance,
            "prediction_error": prediction_error,
            "attention_score": attention_score,
            "novelty": novelty,
        }
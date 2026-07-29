from typing import Dict, Any, Tuple
from ..schemas import EpisodeFrame, EpisodeCandidate


class EpisodeCandidateScorer:
    """
    Evaluates continuous multi-signal evidence across frame metrics, transitions,
    and event tags, maintaining a smooth rolling attention window via exponential decay.
    """

    def __init__(self, config: Any = None) -> None:
        self.config = config

        # Rolling state
        self.rolling_score: float = 0.0

        # Decay factor for exponential rolling attention (0.0 to 1.0)
        self.decay: float = getattr(config, "candidate_decay", 0.85)

        # Default weights for continuous metrics
        self.metric_weights: Dict[str, float] = getattr(
            config,
            "candidate_metric_weights",
            {
                "prediction_error": 0.25,
                "importance": 0.20,
                "novelty": 0.15,
                "attention_score": 0.15,
            },
        )

        # Default weights for discrete transition flags
        self.transition_weights: Dict[str, float] = getattr(
            config,
            "candidate_transition_weights",
            {
                "goal_changed": 0.35,
                "skill_changed": 0.30,
                "target_changed": 0.30,
                "action_changed": 0.25,
            },
        )

        # Default weights for domain event tags
        self.tag_weights: Dict[str, float] = getattr(
            config,
            "candidate_tag_weights",
            {
                "damage_taken": 0.50,
                "food_eaten": 0.40,
                "entered_hazard": 0.35,
                "exited_hazard": 0.20,
                "target_acquired": 0.25,
                "target_lost": 0.20,
                "emotion_spike": 0.30,
                "resource_depleted": 0.30,
            },
        )

    def compute_frame_score(
        self, frame: EpisodeFrame
    ) -> Tuple[float, Dict[str, float], str]:
        """Calculates instantaneous frame score and tracks individual component contributions."""
        contributors: Dict[str, float] = {}

        # 1. Combine continuous metrics
        contributors["prediction_error"] = (
            frame.prediction_error * self.metric_weights.get("prediction_error", 0.25)
        )
        contributors["importance"] = frame.importance * self.metric_weights.get(
            "importance", 0.20
        )
        contributors["novelty"] = frame.novelty * self.metric_weights.get(
            "novelty", 0.15
        )
        contributors["attention_score"] = (
            frame.attention_score * self.metric_weights.get("attention_score", 0.15)
        )

        # 2. Combine transition flags
        for flag, active in frame.transition_flags.items():
            if active and flag in self.transition_weights:
                contributors[f"trans:{flag}"] = self.transition_weights[flag]

        # 3. Combine event tags
        for tag in frame.event_tags:
            if tag in self.tag_weights:
                contributors[f"tag:{tag}"] = self.tag_weights[tag]
            else:
                contributors[f"tag:{tag}"] = 0.10  # fallback boost for unmapped tags

        frame_score = sum(contributors.values())

        # Determine dominant contributor for peak context tracking
        peak_reason = (
            max(contributors.items(), key=lambda x: x[1])[0]
            if contributors
            else "baseline"
        )

        return frame_score, contributors, peak_reason

    def process(self, frame: EpisodeFrame) -> EpisodeCandidate:
        """
        Processes a single frame, updates internal rolling attention score,
        and constructs an EpisodeCandidate instance.
        """
        frame_score, contributors, peak_reason = self.compute_frame_score(frame)

        # Smooth accumulation: rolling_score = (rolling_score * decay) + frame_score
        self.rolling_score = (self.rolling_score * self.decay) + frame_score

        # Calculate confidence metric scaled against rolling accumulation stability
        confidence = min(1.0, self.rolling_score / 1.5)

        return EpisodeCandidate(
            tick=frame.snapshot.tick,
            frame_score=frame_score,
            rolling_score=self.rolling_score,
            confidence=confidence,
            contributors=contributors,
            peak_reason=peak_reason,
        )

    def reset(self) -> None:
        """Resets continuous rolling state."""
        self.rolling_score = 0.0

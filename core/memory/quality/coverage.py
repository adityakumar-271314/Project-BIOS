import math
from typing import Tuple, List
from ..schemas import EpisodicEvent


class CoverageEvaluator:
    """
    Evaluates whether enough of the behavioral event was captured cleanly,
    checking boundary integrity, keyframe temporal dispersion, and metadata completeness.
    """

    def __init__(
        self,
        ideal_keyframe_gap_ratio: float = 0.2,  # Expected keyframe dispersion ratio
    ):
        self.ideal_keyframe_gap_ratio = ideal_keyframe_gap_ratio

    def evaluate(self, event: EpisodicEvent) -> Tuple[float, List[str]]:
        reasons = []
        sig = event.signature
        duration = max(1, sig.duration_ticks)

        # 1. Boundary Completeness Check
        boundary_score = 1.0
        notes = event.notes or ""
        if "truncated" in notes.lower() or duration <= 3:
            boundary_score *= 0.6
            reasons.append("short_or_truncated_duration")

        # 2. Keyframe Temporal Dispersion Check
        kf_ticks = sorted(sig.keyframe_ticks or [kf.tick for kf in event.key_frames])
        if not kf_ticks:
            dispersion_score = 0.2
            reasons.append("missing_keyframes")
        elif len(kf_ticks) == 1:
            dispersion_score = 0.5
            reasons.append("sparse_single_keyframe")
        else:
            # Measure keyframe coverage span over total tick duration
            span = kf_ticks[-1] - kf_ticks[0]
            span_ratio = span / duration

            # Penalize clustered keyframes (e.g., all at start or middle)
            if span_ratio < 0.5:
                dispersion_score = 0.6 + 0.4 * span_ratio
                reasons.append("keyframes_temporally_clustered")
            else:
                dispersion_score = 1.0

        # 3. Signature Summary Completeness
        summary_score = 1.0
        if not sig.resource_summaries or not sig.emotion_summaries:
            summary_score = 0.7
            reasons.append("incomplete_continuous_summaries")

        # Weighted Composite Coverage Score
        coverage = (
            (0.4 * boundary_score) + (0.4 * dispersion_score) + (0.2 * summary_score)
        )
        return round(coverage, 4), reasons

import math
from typing import List, Set
from ..schemas import EpisodeFrame, SparseFrame
from .spatial_context import SpatialContextExtractor
from .config import EpisodeBuilderConfig


class KeyframeExtractor:
    """Performs density-aware keyframe selection using trajectory inflections, tier scoring, and Gaussian suppression."""

    def __init__(self, config: EpisodeBuilderConfig):
        self.config = config
        self.spatial_extractor = SpatialContextExtractor(config)

    def _detect_trajectory_inflections(self, window: List[EpisodeFrame]) -> Set[int]:
        """Identifies ticks where heading or velocity vectors shift significantly past the angular threshold."""
        inflection_ticks = set()
        for i in range(1, len(window) - 1):
            prev_h = window[i - 1].snapshot.heading
            curr_h = window[i].snapshot.heading
            next_h = window[i + 1].snapshot.heading

            diff1 = abs((curr_h - prev_h + math.pi) % (2 * math.pi) - math.pi)
            diff2 = abs((next_h - curr_h + math.pi) % (2 * math.pi) - math.pi)
            if (
                diff1 > self.config.trajectory_threshold_rad
                or diff2 > self.config.trajectory_threshold_rad
            ):
                inflection_ticks.add(window[i].snapshot.tick)
        return inflection_ticks

    def _to_sparse(self, frame: EpisodeFrame) -> SparseFrame:
        """Converts a full EpisodeFrame into a lightweight SparseFrame containing telemetry and spatial contexts."""
        snap = frame.snapshot
        spatial_ctx = self.spatial_extractor.extract(frame)
        return SparseFrame(
            tick=snap.tick,
            pos_x=snap.pos_x,
            pos_y=snap.pos_y,
            vel_x=snap.vel_x,
            vel_y=snap.vel_y,
            heading=snap.heading,
            energy=snap.energy,
            integrity=snap.integrity,
            stress=snap.stress,
            fear=snap.fear,
            drive=snap.drive,
            significance=frame.importance,
            spatial_context=spatial_ctx,
        )

    def extract(self, window: List[EpisodeFrame]) -> List[SparseFrame]:
        """Selects a compressed, diverse set of keyframes from an episode window based on critical anchor weights."""
        if not window:
            return []
        n = len(window)
        trajectory_inflections = self._detect_trajectory_inflections(window)

        base_scores = []
        for frame in window:
            tick = frame.snapshot.tick
            score = 0.0
            if any(
                tag in frame.event_tags
                for tag in (
                    "damage_taken",
                    "food_eaten",
                    "entered_hazard",
                    "left_hazard",
                )
            ):
                score += self.config.anchor_tier_weights["event_critical"]
            if frame.prediction_error > 2.0 or frame.importance > 0.7:
                score += self.config.anchor_tier_weights["state_critical"]
            if tick in trajectory_inflections:
                score += self.config.anchor_tier_weights["trajectory_critical"]
            score += (
                0.2 * frame.importance
                + 0.1 * frame.attention_score
                + 0.1 * frame.novelty
            )
            base_scores.append(score)

        selected_indices: Set[int] = {0, n - 1}
        peak_idx = max(range(n), key=lambda i: base_scores[i])
        selected_indices.add(peak_idx)

        target_count = max(
            self.config.min_keyframes, min(int(n * self.config.compression_ratio), 15)
        )
        effective_scores = list(base_scores)
        sigma = max(self.config.min_sigma_ticks, n * 0.04)

        def _apply_suppression(selected_i: int):
            for i in range(n):
                if i in selected_indices:
                    continue
                dist = abs(window[i].snapshot.tick - window[selected_i].snapshot.tick)
                penalty = math.exp(-0.5 * (dist / sigma) ** 2)
                effective_scores[i] *= (
                    1.0 - self.config.suppression_penalty_factor * penalty
                )

        for idx in list(selected_indices):
            _apply_suppression(idx)

        while len(selected_indices) < target_count:
            best_idx = max(
                (i for i in range(n) if i not in selected_indices),
                key=lambda i: effective_scores[i],
                default=-1,
            )
            if best_idx == -1 or effective_scores[best_idx] < 0.1:
                break
            selected_indices.add(best_idx)
            _apply_suppression(best_idx)

        sorted_indices = sorted(selected_indices)
        return [self._to_sparse(window[i]) for i in sorted_indices]

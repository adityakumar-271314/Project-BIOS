from typing import Optional, Dict, Any
from .episode_builder.builder import EpisodeBuilder
from .boundary.boundary_detector import BoundaryDetector
from .quality.episode_quality import EpisodeQualityEvaluator
from .consolidation.homeostasis_evaluator import HomeostasisEvaluator
from .consolidation.deferred_grouper import DeferredGrouper


class EpisodePipeline:
    def __init__(
        self,
        episodic_memory,
        temporal_buffer,
        boundary_detector: Optional[BoundaryDetector] = None,
        episode_builder: Optional[EpisodeBuilder] = None,
        quality_evaluator: Optional[EpisodeQualityEvaluator] = None,
        homeostasis_evaluator: Optional[HomeostasisEvaluator] = None,
        deferred_grouper: Optional[DeferredGrouper] = None,
    ):
        self.boundary_detector = boundary_detector or BoundaryDetector()
        self.builder = episode_builder or EpisodeBuilder(
            boundary_detector=self.boundary_detector
        )
        self.quality_evaluator = quality_evaluator or EpisodeQualityEvaluator()
        self.temporal_buffer = temporal_buffer
        self.episodic_memory = episodic_memory

        self.homeostasis = homeostasis_evaluator or HomeostasisEvaluator()
        self.deferred_grouper = deferred_grouper or DeferredGrouper(
            metadata_index=self.episodic_memory.archive.index
        )

    def process_candidate(self, candidate_tick: int) -> Dict[str, Any]:
        """
        Runs retrospective boundary detection, episode construction,
        quality filtering, staging, and homeostatic group flushing.
        """
        print(f"[PIPELINE] Retrospective boundary detection & build for tick {candidate_tick}")

        frames = self.temporal_buffer.get_frame_context(
            center_tick=candidate_tick,
            before_ticks=600,
            after_ticks=180,
        )
        if not frames:
            return {"events": []}

        boundaries = self.boundary_detector.detect_boundaries(frames)
        raw_episodes = self.builder.build(frames, boundaries=boundaries)
        if not raw_episodes:
            return {"events": []}

        valid_events = []
        for event in raw_episodes:
            quality, reasons = self.quality_evaluator.evaluate_episode(event, neighbors=raw_episodes)
            event.quality = quality

            if quality.coherence < 0.3 or quality.coverage < 0.4 or quality.overall_quality < 0.25:
                print(f"[PIPELINE] Dropping low-quality episode at start tick {event.start_tick}. Reasons: {reasons}")
                continue

            valid_events.append(event)
            self.deferred_grouper.stage_episode(event)

        if frames and self.deferred_grouper.has_pending:
            latest_frame = frames[-1]
            recent_pred_error = getattr(latest_frame, "prediction_error", 0.0)
            if self.homeostasis.is_safe_for_consolidation(latest_frame.snapshot, recent_pred_error):
                self.deferred_grouper.flush_groups()

        return {"events": valid_events}
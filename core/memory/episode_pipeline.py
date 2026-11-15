from typing import List, Optional, Tuple, Dict, Any
from .episode_builder.builder import EpisodeBuilder
from .boundary.boundary_detector import BoundaryDetector
from .quality.episode_quality import EpisodeQualityEvaluator


class EpisodePipeline:
    def __init__(
        self,
        episodic_memory,
        temporal_buffer,
        boundary_detector: Optional[BoundaryDetector] = None,
        episode_builder: Optional[EpisodeBuilder] = None,
        quality_evaluator: Optional[EpisodeQualityEvaluator] = None,
    ):
        self.boundary_detector = boundary_detector or BoundaryDetector()
        self.builder = episode_builder or EpisodeBuilder(
            boundary_detector=self.boundary_detector
        )
        self.quality_evaluator = quality_evaluator or EpisodeQualityEvaluator()
        self.temporal_buffer = temporal_buffer
        self.episodic_memory = episodic_memory

    def process_candidate(self, candidate_tick: int) -> Dict[str, Any]:
        """
        Runs retrospective boundary detection, episode construction,
        quality filtering, and operational signal annotation.
        """
        print(f"[PIPELINE] Retrospective boundary detection & build for tick {candidate_tick}")

        frames = self.temporal_buffer.get_frame_context(
            center_tick=candidate_tick,
            before_ticks=600,
            after_ticks=180,
        )
        if not frames:
            return {"events": []}

        # 1. Boundary Detection
        boundaries = self.boundary_detector.detect_boundaries(frames)

        # 2. Episode Construction
        raw_episodes = self.builder.build(frames, boundaries=boundaries)
        if not raw_episodes:
            return {"events": []}

        # 3. Quality Evaluation & Operational Gating
        valid_events = []
        for event in raw_episodes:
            quality, reasons = self.quality_evaluator.evaluate_episode(event, neighbors=raw_episodes)
            event.quality = quality

            # Operational Filter: Reject bad construction or extreme redundancy/low quality
            if quality.coherence < 0.3 or quality.coverage < 0.4 or quality.overall_quality < 0.25:
                print(f"[PIPELINE] Dropping low-quality episode at start tick {event.start_tick}. Reasons: {reasons}")
                continue

            valid_events.append(event)

        return {
            "events": valid_events,
        }

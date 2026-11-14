# BEFORE / AFTER modification for core/memory/episode_pipeline.py
from typing import List, Optional, Tuple, Dict, Any
from .episode_builder import EpisodeBuilder
from .boundary.boundary_detector import BoundaryDetector
# REMOVED: from .refinement.episode_refiner import EpisodeRefiner
from .quality.episode_quality import EpisodeQualityEvaluator
# REMOVED: from .hierarchy.hierarchy_builder import HierarchyBuilder
# REMOVED: from .schemas import EpisodicEvent, EpisodeNode, EpisodeHierarchy


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
        and quality evaluation.
        """
        print(f"[PIPELINE] Retrospective boundary detection & build for tick {candidate_tick}")

        # Pull annotated frames from buffer
        frames = self.temporal_buffer.get_frame_context(
            center_tick=candidate_tick,
            before_ticks=600,
            after_ticks=180,
        )
        if not frames:
            return {"events": []}

        # 1. Run boundary detection pipeline to extract clean intervals
        boundaries = self.boundary_detector.detect_boundaries(frames)

        # 2. Build initial candidate events from detected boundaries
        raw_episodes = self.builder.build(frames, boundaries=boundaries)
        if not raw_episodes:
            return {"events": []}

        # 3. Evaluate quality metrics
        quality_evaluated_episodes = self.quality_evaluator.evaluate_batch(
            events=raw_episodes
        )

        return {
            "events": quality_evaluated_episodes,
        }
from typing import List, Optional, Tuple, Dict, Any
from .episode_builder import EpisodeBuilder
from .boundary.boundary_detector import BoundaryDetector
from .refinement.episode_refiner import EpisodeRefiner
from .quality.episode_quality import EpisodeQualityEvaluator
from .hierarchy.hierarchy_builder import HierarchyBuilder
from .schemas import EpisodicEvent, EpisodeNode, EpisodeHierarchy


class EpisodePipeline:
    def __init__(
        self,
        episodic_memory,
        temporal_buffer,
        boundary_detector: Optional[BoundaryDetector] = None,
        episode_builder: Optional[EpisodeBuilder] = None,
        refiner: Optional[EpisodeRefiner] = None,
        quality_evaluator: Optional[EpisodeQualityEvaluator] = None,
        hierarchy_builder: Optional[HierarchyBuilder] = None,
    ):
        self.boundary_detector = boundary_detector or BoundaryDetector()
        self.builder = episode_builder or EpisodeBuilder(
            boundary_detector=self.boundary_detector
        )
        self.refiner = refiner or EpisodeRefiner()
        self.quality_evaluator = quality_evaluator or EpisodeQualityEvaluator()
        self.hierarchy_builder = hierarchy_builder or HierarchyBuilder()
        self.temporal_buffer = temporal_buffer
        self.episodic_memory = episodic_memory

    def process_candidate(self, candidate_tick: int) -> Dict[str, Any]:
        """
        Runs retrospective boundary detection, episode construction, refinement,
        quality evaluation, and Part D hierarchy building.

        Returns a dictionary containing finalized episodes alongside structural
        hierarchy nodes and aggregated hierarchy containers.
        """
        print(
            f"[PIPELINE] Retrospective boundary detection & build for tick {candidate_tick}"
        )

        # 1. Pull annotated frames from buffer
        frames = self.temporal_buffer.get_frame_context(
            center_tick=candidate_tick,
            before_ticks=300,
            after_ticks=180,
        )
        if not frames:
            return {"events": [], "nodes": [], "hierarchies": []}

        # 2. Run boundary detection pipeline to extract clean intervals
        boundaries = self.boundary_detector.detect_boundaries(frames)

        # 3. Build initial candidate events from detected boundaries
        raw_episodes = self.builder.build(frames, boundaries=boundaries)
        if not raw_episodes:
            return {"events": [], "nodes": [], "hierarchies": []}

        # 4. Refine candidate events (Split & Merge post-processing)
        finalized_episodes = self.refiner.refine(events=raw_episodes, frames=frames)
        if not finalized_episodes:
            return {"events": [], "nodes": [], "hierarchies": []}

        # 5. Evaluate quality metrics (Part G analysis pass)
        quality_evaluated_episodes = self.quality_evaluator.evaluate_batch(
            events=finalized_episodes
        )

        # 6. Build Part D Hierarchy (Group -> Mission -> Narrative)
        nodes, hierarchies = self.hierarchy_builder.build_hierarchy(
            events=quality_evaluated_episodes,
            hierarchy_id_prefix=f"candidate_{candidate_tick}",
        )

        return {
            "events": quality_evaluated_episodes,
            "nodes": nodes,
            "hierarchies": hierarchies,
        }

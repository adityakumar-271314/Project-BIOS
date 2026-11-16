from typing import List, Optional, Tuple, Dict, Any
from .episode_builder.builder import EpisodeBuilder
from .boundary.boundary_detector import BoundaryDetector
from .quality.episode_quality import EpisodeQualityEvaluator
from .consolidation.homeostasis_evaluator import HomeostasisEvaluator
from .consolidation.async_consolidator import AsyncConsolidationManager


class EpisodePipeline:
    def __init__(
        self,
        episodic_memory,
        temporal_buffer,
        boundary_detector: Optional[BoundaryDetector] = None,
        episode_builder: Optional[EpisodeBuilder] = None,
        quality_evaluator: Optional[EpisodeQualityEvaluator] = None,
        homeostasis_evaluator: Optional[HomeostasisEvaluator] = None,
        async_consolidator: Optional[AsyncConsolidationManager] = None,
    ):
        self.boundary_detector = boundary_detector or BoundaryDetector()
        self.builder = episode_builder or EpisodeBuilder(
            boundary_detector=self.boundary_detector
        )
        self.quality_evaluator = quality_evaluator or EpisodeQualityEvaluator()
        self.temporal_buffer = temporal_buffer
        self.episodic_memory = episodic_memory

        # Initialize Homeostasis & Asynchronous Consolidation Managers
        self.homeostasis = homeostasis_evaluator or HomeostasisEvaluator()
        self.consolidator = async_consolidator or AsyncConsolidationManager(
            metadata_index=self.episodic_memory.archive.index
        )

    def process_candidate(self, candidate_tick: int) -> Dict[str, Any]:
        """
        Runs retrospective boundary detection, episode construction,
        quality filtering, operational signal annotation, staging for 
        async consolidation, and homeostatic background gating checks.
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

            # --- STEP 3 INTEGRATION: Stage episode metadata for async consolidation ---
            # Builds a lean metadata dictionary matching our unified index structure
            episode_meta = {
                "id": getattr(event, "id", event.start_tick),
                "node_id": f"episode_{event.start_tick:06d}",
                "event_type": event.event_type,
                "start_tick": event.start_tick,
                "end_tick": event.end_tick,
                "peak_tick": event.peak_tick,
                "peak_significance": event.peak_significance,
                "peak_x": event.peak_x,
                "peak_y": event.peak_y,
                "dominant_goal": event.signature.dominant_goal,
                "dominant_skill": event.signature.dominant_skill,
                "outcome_status": event.signature.outcome_status.value if hasattr(event.signature.outcome_status, "value") else event.signature.outcome_status,
                "overall_quality": event.quality.overall_quality if event.quality else 1.0,
                "nearest_landmark_id": event.signature.nearest_landmark_id,
            }
            self.consolidator.stage_episode(episode_meta)

        # --- STEP 2 & 3 INTEGRATION: Homeostatic check & background consolidation trigger ---
        if frames:
            latest_frame = frames[-1]
            recent_pred_error = getattr(latest_frame, "prediction_error", 0.0)
            # Evaluates vitals: if calm/safe, flushes staged items into group summaries
            self.consolidator.tick(
                current_snapshot=latest_frame.snapshot, 
                recent_prediction_error=recent_pred_error
            )

        return {
            "events": valid_events,
        }
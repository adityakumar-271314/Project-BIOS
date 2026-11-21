"""
EpisodePipeline: orchestration only. Order of work for one candidate tick:

    frames -> boundaries -> raw episodes -> quality gate -> encode (archive; ids assigned)
           -> consolidation attempt (calm or overdue) -> result

It owns no storage or grouping logic. Episodes are encoded HERE (and staged for
consolidation by id through EpisodicMemory); callers must not encode them again
(a second encode is harmless - it is detected as a duplicate - but pointless).
Call finalize() at run end so queued episodes are grouped and the hierarchy is saved.
"""

from typing import Any, Dict, List, Optional

from .boundary.boundary_detector import BoundaryDetector
from .consolidation.deferred_grouper import DeferredGrouper
from .consolidation.homeostasis_evaluator import HomeostasisEvaluator
from .episode_builder.builder import EpisodeBuilder
from .quality.episode_quality import EpisodeQualityEvaluator


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
        self.deferred_grouper = deferred_grouper or DeferredGrouper(episodic_memory)

    def process_candidate(self, candidate_tick: int) -> Dict[str, Any]:
        print(
            f"[PIPELINE] Retrospective boundary detection & build for tick {candidate_tick}"
        )
        frames = self.temporal_buffer.get_frame_context(
            center_tick=candidate_tick, before_ticks=600, after_ticks=180
        )
        if not frames:
            return {"events": [], "episode_ids": []}

        boundaries = self.boundary_detector.detect_boundaries(frames)
        raw_episodes = self.builder.build(frames, boundaries=boundaries)
        if not raw_episodes:
            self._consolidate(frames)
            return {"events": [], "episode_ids": []}

        valid_events: List[Any] = []
        episode_ids: List[int] = []
        for event in raw_episodes:
            quality, reasons = self.quality_evaluator.evaluate_episode(
                event, neighbors=raw_episodes
            )
            event.quality = quality
            if (
                quality.coherence < 0.3
                or quality.coverage < 0.4
                or quality.overall_quality < 0.25
            ):
                print(
                    f"[PIPELINE] Dropping low-quality episode at start tick {event.start_tick}. Reasons: {reasons}"
                )
                continue
            valid_events.append(event)
            episode_id = self.episodic_memory.encode(event)
            if episode_id is not None:
                episode_ids.append(episode_id)

        self._consolidate(frames)
        return {"events": valid_events, "episode_ids": episode_ids}

    def _consolidate(self, frames) -> int:
        now_tick = frames[-1].snapshot.tick
        safe = self.homeostasis.is_safe_window(frames)
        return self.deferred_grouper.maybe_flush(safe=safe, now_tick=now_tick)

    def finalize(self) -> int:
        """Flush everything still queued and persist the hierarchy (run end / checkpoint)."""
        return self.deferred_grouper.finalize()

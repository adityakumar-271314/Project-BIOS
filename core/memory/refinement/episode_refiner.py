from typing import List, Optional
from ..schemas import EpisodicEvent, EpisodeFrame
from .split_engine import SplitEngine
from .merge_engine import MergeEngine
from .similarity import SignatureSimilarityEvaluator


class EpisodeRefiner:
    """
    Refines temporary EpisodicEvents produced by EpisodeBuilder using an 
    iterative convergence loop:
    1. Iteratively evaluates splits and merges until structural equilibrium is reached.
    2. Applies dynamic percentage-based keyframe/anchor capping after full stabilization.
    """

    def __init__(
        self,
        split_engine: Optional[SplitEngine] = None,
        merge_engine: Optional[MergeEngine] = None,
        similarity_evaluator: Optional[SignatureSimilarityEvaluator] = None,
        min_keyframe_percentage: float = 0.05,
        max_keyframe_percentage: float = 0.20,
        absolute_min_keyframes: int = 3,
        absolute_max_keyframes: int = 50,
    ):
        self.evaluator = similarity_evaluator or SignatureSimilarityEvaluator()
        self.split_engine = split_engine or SplitEngine()
        self.merge_engine = merge_engine or MergeEngine(
            similarity_evaluator=self.evaluator
        )
        self.min_keyframe_percentage = min_keyframe_percentage
        self.max_keyframe_percentage = max_keyframe_percentage
        self.absolute_min_keyframes = absolute_min_keyframes
        self.absolute_max_keyframes = absolute_max_keyframes

    def refine(
        self,
        events: List[EpisodicEvent],
        frames: Optional[List[EpisodeFrame]] = None,
        max_iterations: int = 3,
    ) -> List[EpisodicEvent]:
        """
        Executes an iterative convergence loop for split and merge passes, 
        ensuring structural stability, followed by dynamic keyframe capping.
        """
        if not events:
            return []

        current_events = list(events)

        # STEP 4: Iterative Convergence Loop
        for iteration in range(max_iterations):
            # Capture structural signature before pass to check for convergence
            prev_signature = [(e.start_tick, e.end_tick, e.peak_tick) for e in current_events]

            # Step 1: Split multi-behavioral episodes
            split_events: List[EpisodicEvent] = []
            for event in current_events:
                splits = self.split_engine.evaluate_splits(event, frames=frames)
                split_events.extend(splits)

            if not split_events:
                current_events = []
                break

            # Step 2: Merge continuous adjacent episodes
            merged_events = self.merge_engine.evaluate_merges(split_events, frames=frames)

            # Check structural signature after merge pass
            curr_signature = [(e.start_tick, e.end_tick, e.peak_tick) for e in merged_events]
            current_events = merged_events

            # Convergence Check: If the event boundaries haven't shifted, we've stabilized
            if prev_signature == curr_signature:
                break

        if not current_events:
            return []

        # Step 3: Apply dynamic post-formation keyframe/anchor capping and thinning
        refined_events = []
        for event in current_events:
            capped_event = self._apply_dynamic_keyframe_capping(event)
            refined_events.append(capped_event)

        return refined_events

    def _apply_dynamic_keyframe_capping(self, event: EpisodicEvent) -> EpisodicEvent:
        """
        Calculates dynamic frame quotas based on total episode duration ticks,
        then thins out excess keyframes after full episode formation.
        """
        if not event.key_frames:
            return event

        duration = max(1, event.end_tick - event.start_tick)

        dynamic_max = int(duration * self.max_keyframe_percentage)
        allowed_max = max(self.absolute_min_keyframes, min(self.absolute_max_keyframes, dynamic_max))

        if len(event.key_frames) <= allowed_max:
            return event

        first_frame = event.key_frames[0]
        last_frame = event.key_frames[-1]
        intermediate = event.key_frames[1:-1]

        sorted_intermediate = sorted(
            intermediate,
            key=lambda kf: getattr(kf, "significance", 0.0),
            reverse=True
        )

        target_intermediate_count = max(0, allowed_max - 2)
        selected_intermediate = sorted_intermediate[:target_intermediate_count]
        selected_intermediate.sort(key=lambda kf: kf.tick)

        event.key_frames = [first_frame] + selected_intermediate + [last_frame]
        return event
from typing import List, Optional, Tuple
from ..schemas import EpisodicEvent, EpisodeFrame
from .split_engine import SplitEngine
from .merge_engine import MergeEngine
from .similarity import SignatureSimilarityEvaluator
from .dynamic_profiler import AdaptiveParameterManager, AdaptiveParameters


class EpisodeRefiner:
    """
    Refines temporary EpisodicEvents produced by EpisodeBuilder using an
    iterative convergence loop and information-entropy dynamic keyframe capping.
    """

    def __init__(
        self,
        parameter_manager: Optional[AdaptiveParameterManager] = None,
        split_engine: Optional[SplitEngine] = None,
        merge_engine: Optional[MergeEngine] = None,
        similarity_evaluator: Optional[SignatureSimilarityEvaluator] = None,
        absolute_min_keyframes: int = 3,
        absolute_max_keyframes: int = 50,
    ):
        self.param_manager = parameter_manager or AdaptiveParameterManager()
        self.evaluator = similarity_evaluator or SignatureSimilarityEvaluator(parameter_manager=self.param_manager)
        self.split_engine = split_engine or SplitEngine(parameter_manager=self.param_manager)
        self.merge_engine = merge_engine or MergeEngine(
            parameter_manager=self.param_manager,
            similarity_evaluator=self.evaluator
        )
        self.absolute_min_keyframes = absolute_min_keyframes
        self.absolute_max_keyframes = absolute_max_keyframes

    def refine(
        self,
        events: List[EpisodicEvent],
        frames: Optional[List[EpisodeFrame]] = None,
        max_iterations: int = 5,
        entropy_tolerance: float = 0.01,
    ) -> List[EpisodicEvent]:
        """
        Executes an adaptive iterative convergence loop for split and merge passes,
        monitoring structural equilibrium via signature entropy change, equipped with
        oscillation circuit-breakers.
        """
        if not events:
            return []

        current_events = list(events)
        signature_history: List[List[Tuple[int, int, int]]] = []

        # STEP 5: Adaptive Iterative Convergence & Circuit Breaker Loop
        for iteration in range(max_iterations):
            # Capture structural signature before pass: (start_tick, end_tick, peak_tick)
            prev_signature = [
                (e.start_tick, e.end_tick, e.peak_tick) for e in current_events
            ]
            signature_history.append(prev_signature)

            # Circuit-Breaker: Check for infinite oscillation loops (e.g. A -> B -> A signature flipping)
            if len(signature_history) >= 3:
                if signature_history[-1] == signature_history[-3]:
                    # Oscillation detected; lock into the most stable configuration and break
                    print(f"[REFINER WARNING] Structural oscillation detected at iteration {iteration}. Forcing convergence lock.")
                    break

            # Step 1: Split multi-behavioral episodes
            split_events: List[EpisodicEvent] = []
            for event in current_events:
                splits = self.split_engine.evaluate_splits(event, frames=frames)
                split_events.extend(splits)

            if not split_events:
                current_events = []
                break

            # Step 2: Merge continuous adjacent episodes
            merged_events = self.merge_engine.evaluate_merges(
                split_events, frames=frames
            )

            # Check structural signature after merge pass
            curr_signature = [
                (e.start_tick, e.end_tick, e.peak_tick) for e in merged_events
            ]
            current_events = merged_events

            # Convergence Check 1: Exact boundary match
            if prev_signature == curr_signature:
                break

            # Convergence Check 2: Fractional Entropy/Shift Tolerance Check
            if len(prev_signature) == len(curr_signature):
                total_tick_shift = sum(
                    abs(p[0] - c[0]) + abs(p[1] - c[1]) 
                    for p, c in zip(prev_signature, curr_signature)
                )
                total_duration = sum(max(1, p[1] - p[0]) for p in prev_signature)
                fractional_change = total_tick_shift / total_duration
                
                if fractional_change < entropy_tolerance:
                    # Changes are trivial; consider system stabilized
                    break

        if not current_events:
            return []

        # Step 3: Apply dynamic post-formation keyframe/anchor capping and thinning
        refined_events = []
        for event in current_events:
            capped_event = self._apply_entropy_keyframe_capping(event)
            refined_events.append(capped_event)

        return refined_events

    def _apply_entropy_keyframe_capping(self, event: EpisodicEvent) -> EpisodicEvent:
        """
        Calculates dynamic frame quotas based on duration ticks and information complexity,
        then thins out excess keyframes using significance grading.
        """
        if not event.key_frames:
            return event

        duration = max(1, event.end_tick - event.start_tick)

        # Fetch adaptive parameters based on event's behavioral complexity
        params = self.param_manager.get_adaptive_parameters(
            current_complexity=event.signature.behavioral_complexity
        )

        # Entropy-driven dynamic budget allocation (scales quota with behavioral complexity)
        complexity_multiplier = max(0.5, min(2.0, 1.0 + event.signature.behavioral_complexity))
        dynamic_max = int(duration * params.max_keyframe_percentage * complexity_multiplier)
        
        allowed_max = max(
            self.absolute_min_keyframes, min(self.absolute_max_keyframes, dynamic_max)
        )

        if len(event.key_frames) <= allowed_max:
            return event

        first_frame = event.key_frames[0]
        last_frame = event.key_frames[-1]
        intermediate = event.key_frames[1:-1]

        # Sort intermediate keyframes by significance score
        sorted_intermediate = sorted(
            intermediate, key=lambda kf: getattr(kf, "significance", 0.0), reverse=True
        )

        target_intermediate_count = max(0, allowed_max - 2)
        selected_intermediate = sorted_intermediate[:target_intermediate_count]
        selected_intermediate.sort(key=lambda kf: kf.tick)

        event.key_frames = [first_frame] + selected_intermediate + [last_frame]
        return event
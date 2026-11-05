from typing import List, Optional
from ..schemas import EpisodicEvent, SparseFrame, EpisodeSignature, EpisodeFrame, StateSummary
from .similarity import SignatureSimilarityEvaluator
from ..episode_builder import EpisodeBuilder
from ..boundary.boundary import BoundaryInterval
from .dynamic_profiler import AdaptiveParameterManager, AdaptiveParameters


class MergeEngine:
    """
    Evaluates temporally adjacent EpisodicEvent instances and merges them
    using dynamic thresholds and scale-relative proximity limits.
    """

    def __init__(
        self,
        parameter_manager: Optional[AdaptiveParameterManager] = None,
        similarity_evaluator: Optional[SignatureSimilarityEvaluator] = None,
        episode_builder: Optional[EpisodeBuilder] = None,
    ):
        self.param_manager = parameter_manager or AdaptiveParameterManager()
        self.evaluator = similarity_evaluator or SignatureSimilarityEvaluator(parameter_manager=self.param_manager)
        self.builder = episode_builder or EpisodeBuilder()

    def _get_dynamic_threshold(
        self, event_a: EpisodicEvent, event_b: EpisodicEvent, base_thresh: float
    ) -> float:
        max_significance = max(event_a.peak_significance, event_b.peak_significance)
        max_novelty = max(
            event_a.signature.overall_novelty, event_b.signature.overall_novelty
        )
        max_hazard = max(
            event_a.signature.max_hazard_exposure, event_b.signature.max_hazard_exposure
        )

        penalty = (
            (0.15 * max_significance)
            + (0.10 * max_novelty)
            + (0.15 * max(0.0, max_hazard))
        )
        threshold = min(0.92, base_thresh + penalty)

        gap = event_b.start_tick - event_a.end_tick
        duration_a = event_a.end_tick - event_a.start_tick
        duration_b = event_b.end_tick - event_b.start_tick
        avg_duration = (duration_a + duration_b) / 2.0

        dynamic_gap_limit = max(15, min(120, int(avg_duration * 0.25)))

        same_category = event_a.event_type == event_b.event_type
        same_goal = (
            event_a.signature.dominant_goal
            and event_a.signature.dominant_goal == event_b.signature.dominant_goal
        )

        if gap <= dynamic_gap_limit and (same_category or same_goal):
            bonus = 0.18 if (same_category and same_goal) else 0.10
            threshold = max(0.38, threshold - bonus)

        return threshold

    def evaluate_merges(
        self, events: List[EpisodicEvent], frames: Optional[List[EpisodeFrame]] = None
    ) -> List[EpisodicEvent]:
        """
        Scans chronological events and iteratively merges them using adaptive parameters.
        """
        if not events or len(events) < 2:
            return events

        sorted_events = sorted(events, key=lambda e: e.start_tick)
        merged_events: List[EpisodicEvent] = []

        curr_event = sorted_events[0]

        for next_event in sorted_events[1:]:
            # Fetch rolling adaptive parameters for this merge check
            avg_complexity = (curr_event.signature.behavioral_complexity + next_event.signature.behavioral_complexity) / 2.0
            params = self.param_manager.get_adaptive_parameters(current_complexity=avg_complexity)

            gap = next_event.start_tick - curr_event.end_tick
            duration_a = curr_event.end_tick - curr_event.start_tick
            duration_b = next_event.end_tick - next_event.start_tick
            avg_duration = (duration_a + duration_b) / 2.0
            dynamic_gap_limit = max(15, min(120, int(avg_duration * 0.25)))

            # 1. Temporal Proximity Check
            if gap > dynamic_gap_limit:
                merged_events.append(curr_event)
                curr_event = next_event
                continue

            # 2. Semantic Interruption Check (using dynamic Z-score thresholds)
            if self.evaluator.check_interruption(
                curr_event.signature, next_event.signature, override_params=params
            ):
                merged_events.append(curr_event)
                curr_event = next_event
                continue

            # 3. Dynamic Threshold & Similarity Evaluation
            dynamic_threshold = self._get_dynamic_threshold(curr_event, next_event, params.base_similarity_threshold)
            sim_score = self.evaluator.compute_similarity(
                curr_event.signature, next_event.signature
            )

            if sim_score >= dynamic_threshold:
                curr_event = self._merge_pair(curr_event, next_event, frames=frames)
            else:
                merged_events.append(curr_event)
                curr_event = next_event

        merged_events.append(curr_event)
        
        # Ingest metrics into profiler to update running statistics
        for ev in merged_events:
            self.param_manager.observe_event({
                "duration": ev.signature.duration_ticks,
                "hazard_exposure": ev.signature.max_hazard_exposure,
                "integrity_delta": ev.signature.resource_summaries.get("integrity", StateSummary(0,0,0,0)).net_change,
                "behavioral_complexity": ev.signature.behavioral_complexity,
            })

        return merged_events

    def _merge_pair(
        self,
        event_a: EpisodicEvent,
        event_b: EpisodicEvent,
        frames: Optional[List[EpisodeFrame]] = None,
    ) -> EpisodicEvent:
        if frames:
            unified_frames = [
                f
                for f in frames
                if event_a.start_tick <= f.snapshot.tick <= event_b.end_tick
            ]
            if unified_frames:
                synthetic_interval = BoundaryInterval(
                    start_tick=unified_frames[0].snapshot.tick,
                    end_tick=unified_frames[-1].snapshot.tick,
                    start_confidence=1.0,
                    end_confidence=1.0,
                    start_reasons=["adaptive_merge_rebuild"],
                    end_reasons=["adaptive_merge_rebuild"],
                )
                built = self.builder.build(
                    unified_frames, boundaries=[synthetic_interval]
                )
                if built:
                    return built[0]

        peak_event = (
            event_a
            if event_a.peak_significance >= event_b.peak_significance
            else event_b
        )

        combined_keyframes_map = {kf.tick: kf for kf in event_a.key_frames}
        for kf in event_b.key_frames:
            combined_keyframes_map[kf.tick] = kf
        sorted_keyframes = [
            combined_keyframes_map[t] for t in sorted(combined_keyframes_map.keys())
        ]

        merged_signature = self._merge_signatures(event_a.signature, event_b.signature)
        merged_notes = f"{event_a.notes or ''} | {event_b.notes or ''}".strip(" |")

        return EpisodicEvent(
            start_tick=event_a.start_tick,
            peak_tick=peak_event.peak_tick,
            end_tick=event_b.end_tick,
            event_type=peak_event.event_type,
            peak_significance=peak_event.peak_significance,
            start_x=event_a.start_x,
            start_y=event_a.start_y,
            peak_x=peak_event.peak_x,
            peak_y=peak_event.peak_y,
            end_x=event_b.end_x,
            end_y=event_b.end_y,
            key_frames=sorted_keyframes,
            signature=merged_signature,
            notes=merged_notes if merged_notes else None,
        )

    def _merge_signatures(
        self,
        sig_a: EpisodeSignature,
        sig_b: EpisodeSignature,
    ) -> EpisodeSignature:
        merged_goal_trans = tuple(
            sorted(
                sig_a.goal_transitions + sig_b.goal_transitions, key=lambda t: t.tick
            )
        )
        merged_skill_trans = tuple(
            sorted(
                sig_a.skill_transitions + sig_b.skill_transitions, key=lambda t: t.tick
            )
        )
        merged_target_trans = tuple(
            sorted(
                sig_a.target_transitions + sig_b.target_transitions,
                key=lambda t: t.tick,
            )
        )

        merged_drivers = tuple(
            sorted(
                set(sig_a.primary_importance_drivers + sig_b.primary_importance_drivers)
            )
        )

        duration = sig_a.duration_ticks + sig_b.duration_ticks

        return EpisodeSignature(
            dominant_goal=sig_a.dominant_goal or sig_b.dominant_goal,
            dominant_skill=sig_a.dominant_skill or sig_b.dominant_skill,
            dominant_target=sig_a.dominant_target or sig_b.dominant_target,
            goal_transitions=merged_goal_trans,
            skill_transitions=merged_skill_trans,
            target_transitions=merged_target_trans,
            outcome_completed=sig_b.outcome_completed,
            resource_summaries=sig_a.resource_summaries,
            emotion_summaries=sig_a.emotion_summaries,
            max_hazard_exposure=max(
                sig_a.max_hazard_exposure, sig_b.max_hazard_exposure
            ),
            max_reward_exposure=max(
                sig_a.max_reward_exposure, sig_b.max_reward_exposure
            ),
            landmark_interactions=max(
                sig_a.landmark_interactions, sig_b.landmark_interactions
            ),
            primary_importance_drivers=merged_drivers,
            duration_ticks=duration,
            behavioral_complexity=(
                sig_a.behavioral_complexity + sig_b.behavioral_complexity
            )
            / 2.0,
            overall_novelty=(sig_a.overall_novelty + sig_b.overall_novelty) / 2.0,
            overall_importance=max(sig_a.overall_importance, sig_b.overall_importance),
        )
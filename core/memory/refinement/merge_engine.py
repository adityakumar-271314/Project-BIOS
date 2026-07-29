from typing import List, Optional
from ..schemas import EpisodicEvent, SparseFrame, EpisodeSignature
from .similarity import SignatureSimilarityEvaluator


class MergeEngine:
    """
    Evaluates temporally adjacent EpisodicEvent instances and merges
    continuous episodes sharing behavioral identity into consolidated events.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.70,
        max_temporal_gap: int = 45,  # Max tick separation to consider merging
        similarity_evaluator: Optional[SignatureSimilarityEvaluator] = None,
    ):
        self.similarity_threshold = similarity_threshold
        self.max_temporal_gap = max_temporal_gap
        self.evaluator = similarity_evaluator or SignatureSimilarityEvaluator()

    def evaluate_merges(self, events: List[EpisodicEvent]) -> List[EpisodicEvent]:
        """
        Scans a chronological list of EpisodicEvent objects and iteratively merges
        adjacent continuous events.
        """
        if not events or len(events) < 2:
            return events

        # Sort events chronologically by start_tick
        sorted_events = sorted(events, key=lambda e: e.start_tick)
        merged_events: List[EpisodicEvent] = []

        curr_event = sorted_events[0]

        for next_event in sorted_events[1:]:
            # 1. Temporal Proximity Check
            gap = next_event.start_tick - curr_event.end_tick
            if gap > self.max_temporal_gap:
                merged_events.append(curr_event)
                curr_event = next_event
                continue

            # 2. Check for Semantic Interruptions
            if self.evaluator.check_interruption(
                curr_event.signature, next_event.signature
            ):
                merged_events.append(curr_event)
                curr_event = next_event
                continue

            # 3. Signature Similarity Evaluation
            sim_score = self.evaluator.compute_similarity(
                curr_event.signature, next_event.signature
            )

            if sim_score >= self.similarity_threshold:
                # Continuous behavioral identity confirmed -> Merge next into curr
                curr_event = self._merge_pair(curr_event, next_event)
            else:
                merged_events.append(curr_event)
                curr_event = next_event

        merged_events.append(curr_event)
        return merged_events

    def _merge_pair(
        self, event_a: EpisodicEvent, event_b: EpisodicEvent
    ) -> EpisodicEvent:
        """
        Consolidates two adjacent EpisodicEvents into a single merged EpisodicEvent.
        """
        # Determine overall peak snapshot based on higher significance
        peak_event = (
            event_a
            if event_a.peak_significance >= event_b.peak_significance
            else event_b
        )

        # Combine sparse keyframes, ensuring uniqueness and chronological order
        combined_keyframes_map = {kf.tick: kf for kf in event_a.key_frames}
        for kf in event_b.key_frames:
            combined_keyframes_map[kf.tick] = kf
        sorted_keyframes = [
            combined_keyframes_map[t] for t in sorted(combined_keyframes_map.keys())
        ]

        # Consolidated Signature
        merged_signature = self._merge_signatures(
            event_a.signature, event_b.signature, sorted_keyframes
        )

        # Merge Notes View
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
            max_fear=max(event_a.max_fear, event_b.max_fear),
            avg_fear=(event_a.avg_fear + event_b.avg_fear) / 2.0,
            max_stress=max(event_a.max_stress, event_b.max_stress),
            avg_stress=(event_a.avg_stress + event_b.avg_stress) / 2.0,
            max_drive=max(event_a.max_drive, event_b.max_drive),
            avg_drive=(event_a.avg_drive + event_b.avg_drive) / 2.0,
            energy_delta=event_a.energy_delta + event_b.energy_delta,
            integrity_delta=event_a.integrity_delta + event_b.integrity_delta,
            peak_snapshot=peak_event.peak_snapshot,
            key_frames=sorted_keyframes,
            signature=merged_signature,
            notes=merged_notes if merged_notes else None,
        )

    def _merge_signatures(
        self,
        sig_a: EpisodeSignature,
        sig_b: EpisodeSignature,
        keyframes: List[SparseFrame],
    ) -> EpisodeSignature:
        """
        Combines two immutable EpisodeSignature instances into a unified signature.
        """
        # Combine goal, skill, and target transitions chronologically
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

        # Merge primary importance drivers
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
            outcome_completed=sig_b.outcome_completed,  # Takes final outcome
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
            keyframe_ticks=tuple(kf.tick for kf in keyframes),
        )

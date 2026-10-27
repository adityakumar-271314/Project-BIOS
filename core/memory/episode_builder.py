from .boundary.boundary import BoundaryInterval
from .boundary.boundary_detector import BoundaryDetector
import math
from typing import List, Dict, Set, Tuple, Optional
from collections import Counter
from .schemas import (
    EpisodicEvent,
    EpisodeFrame,
    SparseFrame,
    EpisodeSignature,
    StateSummary,
    BehavioralTransition,
)


class EpisodeBuilder:
    """
    Pure computational worker for constructing EpisodicEvent instances from
    annotated EpisodeFrame sequences and BoundaryIntervals.
    """
    def __init__(
        self,
        compression_ratio: float = 0.03,
        min_keyframes: int = 3,
        change_threshold: float = 0.25,
        boundary_detector: Optional[BoundaryDetector] = None,
        pre_peak_runway_ticks: int = 50,  # Added buffer configuration for pre-peak runway
    ):
        self.COMPRESSION_RATIO = compression_ratio
        self.MIN_KEYFRAMES = min_keyframes
        self.CHANGE_THRESHOLD = change_threshold
        self.boundary_detector = boundary_detector or BoundaryDetector()
        self.pre_peak_runway_ticks = pre_peak_runway_ticks

    def build(
        self,
        frames: List[EpisodeFrame],
        boundaries: Optional[List[BoundaryInterval]] = None,
    ) -> List[EpisodicEvent]:
        if not frames:
            return []

        if boundaries is None:
            boundaries = self.boundary_detector.detect_boundaries(frames)

        if not boundaries:
            return []

        frame_map = {f.snapshot.tick: f for f in frames}
        sorted_ticks = sorted(frame_map.keys())
        min_available_tick = sorted_ticks[0]

        episodes = []

        for idx, interval in enumerate(boundaries):
            prev_end_tick = (
                boundaries[idx - 1].end_tick 
                if idx > 0 
                else min_available_tick
            )

            # 1. Preliminary window slice to locate peak frame and assess dynamics
            prelim_frames = [
                frame_map[t] for t in sorted_ticks 
                if interval.start_tick <= t <= interval.end_tick
            ]
            if not prelim_frames:
                continue
            
            peak_frame = max(prelim_frames, key=lambda f: f.importance)
            peak_tick = peak_frame.snapshot.tick

            # 2. Robust Dynamic Pre-Peak Runway (Lookback Gradient)
            # Look backward from interval.start_tick (or peak) to find where anticipation started rising
            # (i.e., where stress, fear, or attention were elevated above resting baseline).
            expanded_start_tick = interval.start_tick
            for f in reversed(sorted_ticks):
                if f >= interval.start_tick:
                    continue
                if f < prev_end_tick or f < min_available_tick:
                    break
                
                frame_obj = frame_map[f]
                # If vitals/attention/prediction error show active anticipation/buildup, expand backward
                if (frame_obj.snapshot.stress > 0.15 or 
                    frame_obj.snapshot.fear > 0.15 or 
                    frame_obj.prediction_error > 0.8 or 
                    frame_obj.attention_score > 0.3):
                    expanded_start_tick = f
                else:
                    # Hit baseline; stop expanding backward
                    break

            # If expansion was too minimal, guarantee a proportional runway based on event distance to peak
            min_runway_ticks = int((peak_tick - interval.start_tick) * 0.5)
            fallback_start = max(interval.start_tick - max(25, min_runway_ticks), prev_end_tick, min_available_tick)
            expanded_start_tick = min(expanded_start_tick, fallback_start)

            # Post-peak dynamic taper (clip trailing idle ticks where attention/importance drop)
            trimmed_end_tick = interval.end_tick
            for f in reversed(prelim_frames):
                if f.snapshot.tick <= peak_frame.snapshot.tick:
                    break
                if f.attention_score < 0.2 and f.importance < 0.3:
                    trimmed_end_tick = f.snapshot.tick
                else:
                    break

            # Final window frames using dynamic asymmetric bounds
            window_frames = [
                frame_map[t]
                for t in sorted_ticks
                if expanded_start_tick <= t <= trimmed_end_tick
            ]

            if not window_frames:
                continue

            # Re-verify peak within the final asymmetric window
            peak_frame = max(window_frames, key=lambda f: f.importance)
            first_snap = window_frames[0].snapshot
            last_snap = window_frames[-1].snapshot

            # Density-aware keyframe selection with heavy reduction
            key_frames = self._extract_key_frames(window_frames)
            signature = self._build_signature(window_frames, key_frames)

            start_reasons_str = ",".join(interval.start_reasons)
            end_reasons_str = ",".join(interval.end_reasons)
            notes_str = f"Start: [{start_reasons_str}] (Asymmetric) | End: [{end_reasons_str}]"
            if peak_frame.snapshot.notes:
                notes_str += f" | {peak_frame.snapshot.notes}"

            episode = EpisodicEvent(
                start_tick=first_snap.tick,
                peak_tick=peak_frame.snapshot.tick,
                end_tick=last_snap.tick,
                event_type=peak_frame.event_type,
                peak_significance=peak_frame.importance,
                start_x=first_snap.pos_x,
                start_y=first_snap.pos_y,
                peak_x=peak_frame.snapshot.pos_x,
                peak_y=peak_frame.snapshot.pos_y,
                end_x=last_snap.pos_x,
                end_y=last_snap.pos_y,
                peak_snapshot=peak_frame.snapshot,
                key_frames=key_frames,
                signature=signature,
                notes=notes_str,
            )
            episodes.append(episode)

        return episodes


    def _build_signature(
        self, window: List[EpisodeFrame], keyframes: List[SparseFrame]
    ) -> EpisodeSignature:
        """
        Extracts high-level behavioral identity and summary descriptors without
        duplicating per-frame temporal telemetry or keyframe contents.
        """
        if not window:
            return EpisodeSignature()

        # 1. Determine Dominant States
        goals = [f.snapshot.goal_name for f in window if f.snapshot.goal_name]
        skills = [f.snapshot.active_skill for f in window if f.snapshot.active_skill]
        targets = [f.snapshot.target_type for f in window if f.snapshot.target_type]

        dom_goal = Counter(goals).most_common(1)[0][0] if goals else None
        dom_skill = Counter(skills).most_common(1)[0][0] if skills else None
        dom_target = Counter(targets).most_common(1)[0][0] if targets else None

        # 2. Extract Significant Transitions (Only when state actually changes)
        goal_trans: List[BehavioralTransition] = []
        skill_trans: List[BehavioralTransition] = []
        target_trans: List[BehavioralTransition] = []

        for i in range(1, len(window)):
            prev, curr = window[i - 1].snapshot, window[i].snapshot
            if curr.goal_name != prev.goal_name:
                goal_trans.append(
                    BehavioralTransition(curr.tick, prev.goal_name, curr.goal_name)
                )
            if curr.active_skill != prev.active_skill:
                skill_trans.append(
                    BehavioralTransition(
                        curr.tick, prev.active_skill, curr.active_skill
                    )
                )
            if curr.target_type != prev.target_type:
                target_trans.append(
                    BehavioralTransition(curr.tick, prev.target_type, curr.target_type)
                )

        # 3. Summarize Continuous State Evolution
        def _summarize(vals: List[float]) -> StateSummary:
            return StateSummary(
                initial=vals[0],
                final=vals[-1],
                min_val=min(vals),
                max_val=max(vals),
            )

        resource_summaries = {
            "energy": _summarize([f.snapshot.energy for f in window]),
            "integrity": _summarize([f.snapshot.integrity for f in window]),
        }

        emotion_summaries = {
            "fear": _summarize([f.snapshot.fear for f in window]),
            "stress": _summarize([f.snapshot.stress for f in window]),
            "drive": _summarize([f.snapshot.drive for f in window]),
        }

        # 4. Environment & Retention Descriptors
        max_hazard = max(f.snapshot.hazard_stim for f in window)
        max_reward = max(f.snapshot.food_stim for f in window)
        landmarks = max(f.snapshot.visible_landmarks for f in window)

        # Identify key drivers for retaining this episode
        drivers = set()
        if any(f.novelty > 0.4 for f in window):
            drivers.add("high_novelty")
        if goal_trans or skill_trans:
            drivers.add("behavioral_shift")
        if max_hazard > 0.5:
            drivers.add("hazard_exposure")
        if max_reward > 0.5:
            drivers.add("reward_acquisition")
        if abs(resource_summaries["integrity"].net_change) > 0.15:
            drivers.add("integrity_change")

        # 5. Descriptive Statistics
        complexity = (len(goal_trans) + len(skill_trans) + len(target_trans)) / max(
            1, len(window)
        )
        avg_novelty = sum(f.novelty for f in window) / len(window)
        max_importance = max(f.importance for f in window)
        duration = window[-1].snapshot.tick - window[0].snapshot.tick + 1

        # In core/memory/episode_builder.py (Inside _build_signature)

        return EpisodeSignature(
            dominant_goal=dom_goal,
            dominant_skill=dom_skill,
            dominant_target=dom_target,
            goal_transitions=tuple(goal_trans),
            skill_transitions=tuple(skill_trans),
            target_transitions=tuple(target_trans),
            outcome_completed=(window[-1].snapshot.action_state == "complete"),
            resource_summaries=resource_summaries,
            emotion_summaries=emotion_summaries,
            max_hazard_exposure=max_hazard,
            max_reward_exposure=max_reward,
            landmark_interactions=landmarks,
            primary_importance_drivers=tuple(sorted(drivers)),
            duration_ticks=duration,
            behavioral_complexity=complexity,
            overall_novelty=avg_novelty,
            overall_importance=max_importance,
        )



    def _extract_key_frames(self, window: List[EpisodeFrame]) -> List[SparseFrame]:
        """
        Density-Aware, Dynamic Percentage-Based Keyframe Selection.

        Calculates initial keyframe scores based on importance, novelty, transitions,
        and candidates. Iteratively selects the highest scoring frame and applies Gaussian
        density suppression to nearby frames, encouraging diversity while preserving high-information clusters.
        """

        if not window:
            return []

        n = len(window)

        # Heavily reduced target budget ratios to ensure a big decrease in keyframes
        adaptive_ratio = max(0.03, 0.10 - (0.0001 * n))
        min_limit = max(3, int(n * 0.02))
        max_limit = min(20, int(n * 0.10))
        
        target_count = int(n * adaptive_ratio)
        target_count = max(min_limit, min(target_count, max_limit))
        target_count = min(target_count, n)

        base_scores = []
        for frame in window:
            score = (
                0.4 * frame.importance
                + 0.2 * frame.novelty
                + 0.2 * frame.attention_score
                + 0.1 * frame.prediction_error
            )
            if any(frame.transition_flags.values()):
                score += 0.15
            base_scores.append(score)

        effective_scores = list(base_scores)
        selected_indices: Set[int] = set()

        selected_indices.add(0)
        selected_indices.add(n - 1)
        peak_idx = max(range(n), key=lambda i: base_scores[i])
        selected_indices.add(peak_idx)

        sigma = max(2.0, n * 0.05)

        def _apply_suppression(selected_i: int):
            for i in range(n):
                if i in selected_indices:
                    continue
                dist = abs(window[i].snapshot.tick - window[selected_i].snapshot.tick)
                penalty = math.exp(-0.5 * (dist / sigma) ** 2)
                effective_scores[i] *= 1.0 - 0.6 * penalty

        for idx in list(selected_indices):
            _apply_suppression(idx)

        while len(selected_indices) < target_count:
            best_idx = -1
            best_score = -1.0

            for i in range(n):
                if i not in selected_indices and effective_scores[i] > best_score:
                    best_score = effective_scores[i]
                    best_idx = i

            if best_idx == -1:
                break

            selected_indices.add(best_idx)
            _apply_suppression(best_idx)

        sorted_indices = sorted(selected_indices)
        return [self._to_sparse(window[i]) for i in sorted_indices]

    def _to_sparse(self, frame: EpisodeFrame) -> SparseFrame:
        snap = frame.snapshot
        return SparseFrame(
            tick=snap.tick,
            pos_x=snap.pos_x,
            pos_y=snap.pos_y,
            vel_x=snap.vel_x,
            vel_y=snap.vel_y,
            heading=snap.heading,
            energy=snap.energy,
            integrity=snap.integrity,
            stress=snap.stress,
            fear=snap.fear,
            drive=snap.drive,
            significance=frame.importance,
        )

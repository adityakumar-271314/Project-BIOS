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
    def __init__(
        self,
        compression_ratio: float = 0.08,
        min_keyframes: int = 5,
        change_threshold: float = 0.25,
        boundary_detector: Optional[BoundaryDetector] = None,
    ):
        """
        Pure computational worker for constructing EpisodicEvent instances from 
        annotated EpisodeFrame sequences and BoundaryIntervals.
        """
        self.COMPRESSION_RATIO = compression_ratio
        self.MIN_KEYFRAMES = min_keyframes
        self.CHANGE_THRESHOLD = change_threshold
        self.boundary_detector = boundary_detector or BoundaryDetector()

    def build(
        self,
        frames: List[EpisodeFrame],
        boundaries: Optional[List[BoundaryInterval]] = None,
    ) -> List[EpisodicEvent]:
        """
        Transforms frames into consolidated EpisodicEvents using BoundaryIntervals.
        If boundaries are not provided, uses the BoundaryDetector to extract them.
        """
        if not frames:
            return []

        # Step 1: Obtain Boundary Intervals if not pre-computed
        if boundaries is None:
            boundaries = self.boundary_detector.detect_boundaries(frames)

        if not boundaries:
            return []

        # Map frames by tick for fast lookup
        frame_map = {f.snapshot.tick: f for f in frames}
        sorted_ticks = sorted(frame_map.keys())

        episodes = []

        # Step 2: Build EpisodicEvents for each validated BoundaryInterval
        for interval in boundaries:
            # Extract frames within [start_tick, end_tick]
            window_frames = [
                frame_map[t]
                for t in sorted_ticks
                if interval.start_tick <= t <= interval.end_tick
            ]

            if not window_frames:
                continue

            # Identify peak frame by highest importance score
            peak_frame = max(window_frames, key=lambda f: f.importance)
            first_snap = window_frames[0].snapshot
            last_snap = window_frames[-1].snapshot

            # Step 2a: Density-aware keyframe selection
            key_frames = self._extract_key_frames(window_frames)

            # Step 2b: Build immutable behavioral EpisodeSignature
            signature = self._build_signature(window_frames, key_frames)

            # Construct optional secondary notes view (including boundary reasons)
            start_reasons_str = ",".join(interval.start_reasons)
            end_reasons_str = ",".join(interval.end_reasons)
            notes_str = f"Start: [{start_reasons_str}] | End: [{end_reasons_str}]"
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
                max_fear=max(f.snapshot.fear for f in window_frames),
                avg_fear=sum(f.snapshot.fear for f in window_frames) / len(window_frames),
                max_stress=max(f.snapshot.stress for f in window_frames),
                avg_stress=sum(f.snapshot.stress for f in window_frames) / len(window_frames),
                max_drive=max(f.snapshot.drive for f in window_frames),
                avg_drive=sum(f.snapshot.drive for f in window_frames) / len(window_frames),
                energy_delta=last_snap.energy - first_snap.energy,
                integrity_delta=last_snap.integrity - first_snap.integrity,
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
                    BehavioralTransition(curr.tick, prev.active_skill, curr.active_skill)
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
        complexity = (len(goal_trans) + len(skill_trans) + len(target_trans)) / max(1, len(window))
        avg_novelty = sum(f.novelty for f in window) / len(window)
        max_importance = max(f.importance for f in window)
        duration = window[-1].snapshot.tick - window[0].snapshot.tick + 1

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
            keyframe_ticks=tuple(kf.tick for kf in keyframes),
        )

    def _extract_key_frames(self, window: List[EpisodeFrame]) -> List[SparseFrame]:
        """
        Density-Aware Keyframe Selection.
        
        Calculates initial keyframe scores based on importance, novelty, transitions,
        and candidates. Iteratively selects the highest scoring frame and applies Gaussian
        density suppression to nearby frames, encouraging diversity while preserving high-information clusters.
        """
        if not window:
            return []

        n = len(window)
        target_count = max(self.MIN_KEYFRAMES, int(n * self.COMPRESSION_RATIO))
        target_count = min(target_count, n)

        # Step 1: Compute initial multi-factor keyframe scores
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

        # Always seed with the boundary start, end, and peak frame
        selected_indices.add(0)
        selected_indices.add(n - 1)
        peak_idx = max(range(n), key=lambda i: base_scores[i])
        selected_indices.add(peak_idx)

        # Dynamic decay length scale proportional to window duration
        sigma = max(2.0, n * 0.05)

        def _apply_suppression(selected_i: int):
            """Softly dampens nearby scores to encourage temporal diversity."""
            for i in range(n):
                if i in selected_indices:
                    continue
                dist = abs(window[i].snapshot.tick - window[selected_i].snapshot.tick)
                penalty = math.exp(-0.5 * (dist / sigma) ** 2)
                # Dampen score up to 60% based on proximity
                effective_scores[i] *= (1.0 - 0.6 * penalty)

        # Apply suppression for initial seeds
        for idx in list(selected_indices):
            _apply_suppression(idx)

        # Step 2: Iteratively select highest scoring unselected frame until target budget is reached
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
            active_skill=snap.active_skill,
            action_state=snap.action_state,
            target_type=snap.target_type,
            visible_food=snap.visible_food,
            visible_hazards=snap.visible_hazards,
            notes=snap.notes,
        )
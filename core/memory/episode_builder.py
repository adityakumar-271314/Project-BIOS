from typing import List, Optional
from .schemas import EpisodicEvent, EpisodeFrame, SparseFrame
from .boundary.boundary import BoundaryInterval
from .boundary.boundary_detector import BoundaryDetector


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

            key_frames = self._extract_key_frames(window_frames)

            # Construct consolidated notes including boundary reasons
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
                notes=notes_str,
            )
            episodes.append(episode)

        return episodes

    def _extract_key_frames(self, window: List[EpisodeFrame]) -> List[SparseFrame]:
        """Selection of sparse keyframes across window duration."""
        if not window:
            return []

        n = len(window)
        key_frames = []
        used_indices = set()

        # Always include boundary anchors
        key_frames.append(self._to_sparse(window[0]))
        used_indices.add(0)

        peak_idx = max(range(n), key=lambda i: window[i].importance)
        if peak_idx not in used_indices:
            key_frames.append(self._to_sparse(window[peak_idx]))
            used_indices.add(peak_idx)

        if n > 1:
            last_idx = n - 1
            if last_idx not in used_indices:
                key_frames.append(self._to_sparse(window[last_idx]))
                used_indices.add(last_idx)

        # Dynamic change detection for intermediate keyframes
        for i in range(1, n):
            prev = window[i - 1].snapshot
            curr = window[i].snapshot
            curr_frame = window[i]

            stress_change = abs(curr.stress - prev.stress)
            fear_change = abs(curr.fear - prev.fear)
            drive_change = abs(curr.drive - prev.drive)
            imp_change = abs(curr_frame.importance - window[i - 1].importance)

            if (
                stress_change > 0.15
                or fear_change > 0.15
                or drive_change > 0.15
                or imp_change > 0.1
                or curr_frame.transition_flags.get("skill_shift", False)
                or curr_frame.transition_flags.get("target_shift", False)
            ):
                if i not in used_indices:
                    key_frames.append(self._to_sparse(curr_frame))
                    used_indices.add(i)

        # Fill to target budget with remaining highest importance frames
        target = max(self.MIN_KEYFRAMES, int(n * self.COMPRESSION_RATIO))
        if len(key_frames) < target:
            candidates = []
            for i in range(n):
                if i not in used_indices:
                    score = (
                        window[i].importance
                        + abs(window[i].snapshot.fear) * 0.3
                        + abs(window[i].snapshot.stress) * 0.3
                        + abs(window[i].snapshot.drive) * 0.2
                    )
                    candidates.append((score, i))

            candidates.sort(reverse=True)
            for _, idx in candidates[: target - len(key_frames)]:
                key_frames.append(self._to_sparse(window[idx]))

        key_frames.sort(key=lambda kf: kf.tick)
        return key_frames

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
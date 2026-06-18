from typing import List
from .schemas import EpisodicEvent, EpisodeFrame, SparseFrame

class EpisodeBuilder:
    def __init__(self, low_threshold: float = 0.25, merge_overlap: bool = True,
                 compression_ratio: float = 0.08, min_keyframes: int = 5,
                 change_threshold: float = 0.25):
        """
        Pure computational worker for temporal compression and episode extraction.

        Args:
            low_threshold: The significance floor used for boundary hysteresis.
            merge_overlap: Whether to consolidate overlapping temporal intervals.
        """
        self.LOW_THRESHOLD = low_threshold
        self.MERGE_OVERLAP = merge_overlap
        self.COMPRESSION_RATIO = compression_ratio
        self.MIN_KEYFRAMES = min_keyframes
        self.CHANGE_THRESHOLD = change_threshold

    def build(self, frames: List[EpisodeFrame]) -> List[EpisodicEvent]:
        """
        Transforms a continuous sequence of annotated frames into distinct, consolidated events.
        
        Args:
            frames: Chronological list of EpisodeFrame objects received from the buffer context.
            
        Returns:
            A list of constructed, summarized EpisodicEvent objects.
        """
        if not frames:
            return []

        # --- Responsibility 1 & 2: Find and Filter Candidate Peaks --- (unchanged)
        peak_indices = []
        for i in range(1, len(frames) - 1):
            current = frames[i]
            prev_frame = frames[i - 1]
            next_frame = frames[i + 1]
            if current.significance > prev_frame.significance and current.significance >= next_frame.significance:
                if current.significance > self.LOW_THRESHOLD:
                    peak_indices.append(i)

        if not peak_indices:
            return []

        # --- Responsibility 3 & 4: Expand Regions & Apply Hysteresis --- (unchanged)
        raw_intervals = []
        for peak_idx in peak_indices:
            start_idx = peak_idx
            while start_idx > 0 and frames[start_idx].significance > self.LOW_THRESHOLD:
                start_idx -= 1
            if frames[start_idx].significance <= self.LOW_THRESHOLD and start_idx < peak_idx:
                start_idx += 1

            end_idx = peak_idx
            while end_idx < len(frames) - 1 and frames[end_idx].significance > self.LOW_THRESHOLD:
                end_idx += 1
            if frames[end_idx].significance <= self.LOW_THRESHOLD and end_idx > peak_idx:
                end_idx -= 1

            raw_intervals.append((start_idx, end_idx))

        # --- Responsibility 5: Merge Overlapping Regions --- (unchanged)
        if self.MERGE_OVERLAP and len(raw_intervals) > 1:
            raw_intervals.sort(key=lambda x: x[0])
            merged_intervals = [raw_intervals[0]]
            for current_start, current_end in raw_intervals[1:]:
                last_start, last_end = merged_intervals[-1]
                if current_start <= last_end:
                    merged_intervals[-1] = (last_start, max(last_end, current_end))
                else:
                    merged_intervals.append((current_start, current_end))
            intervals = merged_intervals
        else:
            intervals = raw_intervals

        # --- Build Persistent Episodes from Intervals --- (core logic same)
        episodes = []
        for start_idx, end_idx in intervals:
            window_frames = frames[start_idx : end_idx + 1]
            if not window_frames:
                continue

            peak_frame = max(window_frames, key=lambda f: f.significance)
            first_snap = window_frames[0].snapshot
            last_snap = window_frames[-1].snapshot

            key_frames = self._extract_key_frames(window_frames)

            episode = EpisodicEvent(
                start_tick=first_snap.tick,
                peak_tick=peak_frame.snapshot.tick,
                end_tick=last_snap.tick,
                event_type=peak_frame.event_type,
                peak_significance=peak_frame.significance,
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
                notes=peak_frame.snapshot.notes
            )
            episodes.append(episode)
        return episodes

    def _extract_key_frames(self, window: List[EpisodeFrame]) -> List[SparseFrame]:
        """helper - simple, stable change + budget based selection."""
        if not window:
            return []

        n = len(window)
        key_frames = []
        used_indices = set()

        # Always include anchors
        key_frames.append(self._to_sparse(window[0]))
        used_indices.add(0)

        peak_idx = max(range(n), key=lambda i: window[i].significance)
        if peak_idx not in used_indices:
            key_frames.append(self._to_sparse(window[peak_idx]))
            used_indices.add(peak_idx)

        if n > 1:
            last_idx = n - 1
            if last_idx not in used_indices:
                key_frames.append(self._to_sparse(window[last_idx]))
                used_indices.add(last_idx)

        # Simple change detection (absolute + relative, stable near zero)
        for i in range(1, n):
            prev = window[i-1].snapshot
            curr = window[i].snapshot
            curr_frame = window[i]

            stress_change = abs(curr.stress - prev.stress)
            fear_change = abs(curr.fear - prev.fear)
            drive_change = abs(curr.drive - prev.drive)
            sig_change = abs(curr_frame.significance - window[i-1].significance)

            rel_stress = stress_change / (abs(prev.stress) + 1e-5)
            rel_fear = fear_change / (abs(prev.fear) + 1e-5)
            rel_drive = drive_change / (abs(prev.drive) + 1e-5)

            if (stress_change > 0.15 or fear_change > 0.15 or drive_change > 0.15 or
                sig_change > 0.1 or rel_stress > self.CHANGE_THRESHOLD or
                rel_fear > self.CHANGE_THRESHOLD or rel_drive > self.CHANGE_THRESHOLD or
                (prev.active_skill != curr.active_skill) or
                (prev.target_type != curr.target_type)):
                if i not in used_indices:
                    key_frames.append(self._to_sparse(curr_frame))
                    used_indices.add(i)

        # Fill to target budget with highest significance remaining frames
        target = max(self.MIN_KEYFRAMES, int(n * self.COMPRESSION_RATIO))
        if len(key_frames) < target:
            candidates = []
            for i in range(n):
                if i not in used_indices:
                    score = window[i].significance + abs(window[i].snapshot.fear) * 0.3 + \
                            abs(window[i].snapshot.stress) * 0.3 + abs(window[i].snapshot.drive) * 0.2
                    candidates.append((score, i))

            candidates.sort(reverse=True)
            for _, idx in candidates[:target - len(key_frames)]:
                key_frames.append(self._to_sparse(window[idx]))

        # Sort by tick
        key_frames.sort(key=lambda kf: kf.tick)
        return key_frames

    def _to_sparse(self, frame: EpisodeFrame) -> SparseFrame:
        snap = frame.snapshot
        return SparseFrame(
            tick=snap.tick,
            pos_x=snap.pos_x, pos_y=snap.pos_y,
            vel_x=snap.vel_x, vel_y=snap.vel_y,
            heading=snap.heading,
            energy=snap.energy,
            integrity=snap.integrity,
            stress=snap.stress,
            fear=snap.fear,
            drive=snap.drive,
            significance=frame.significance,
            active_skill=snap.active_skill,
            action_state=snap.action_state,
            target_type=snap.target_type,
            visible_food=snap.visible_food,
            visible_hazards=snap.visible_hazards,
            notes=snap.notes
        )
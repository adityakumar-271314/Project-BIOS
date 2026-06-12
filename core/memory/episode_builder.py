from typing import List
from .schemas import EpisodicEvent, EpisodeFrame

class EpisodeBuilder:
    def __init__(self, low_threshold: float = 0.25, merge_overlap: bool = True):
        """
        Pure computational worker for temporal compression and episode extraction.
        
        Args:
            low_threshold: The significance floor used for boundary hysteresis.
            merge_overlap: Whether to consolidate overlapping temporal intervals.
        """
        self.LOW_THRESHOLD = low_threshold
        self.MERGE_OVERLAP = merge_overlap

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

        # --- Responsibility 1 & 2: Find and Filter Candidate Peaks ---
        peak_indices = []
        for i in range(1, len(frames) - 1):
            current = frames[i]
            prev_frame = frames[i - 1]
            next_frame = frames[i + 1]

            # Local maximum check
            if current.significance > prev_frame.significance and current.significance >= next_frame.significance:
                # Reject tiny peaks (noise filtering)
                if current.significance > self.LOW_THRESHOLD:
                    peak_indices.append(i)

        if not peak_indices:
            return []

        # --- Responsibility 3 & 4: Expand Regions & Apply Hysteresis ---
        raw_intervals = []
        for peak_idx in peak_indices:
            # Expand backwards until significance drops below the hysteresis floor
            start_idx = peak_idx
            while start_idx > 0 and frames[start_idx].significance > self.LOW_THRESHOLD:
                start_idx -= 1
            # If we exited due to hitting the threshold, step back forward into the valid window
            if frames[start_idx].significance <= self.LOW_THRESHOLD and start_idx < peak_idx:
                start_idx += 1

            # Expand forwards until significance drops below the hysteresis floor
            end_idx = peak_idx
            while end_idx < len(frames) - 1 and frames[end_idx].significance > self.LOW_THRESHOLD:
                end_idx += 1
            # If we exited due to hitting the threshold, step back backward into the valid window
            if frames[end_idx].significance <= self.LOW_THRESHOLD and end_idx > peak_idx:
                end_idx -= 1

            raw_intervals.append((start_idx, end_idx))

        # --- Responsibility 5: Merge Overlapping Regions ---
        if self.MERGE_OVERLAP and len(raw_intervals) > 1:
            # Ensure sort order by start index
            raw_intervals.sort(key=lambda x: x[0])
            merged_intervals = [raw_intervals[0]]

            for current_start, current_end in raw_intervals[1:]:
                last_start, last_end = merged_intervals[-1]

                # Check for overlap or immediate adjacency
                if current_start <= last_end:
                    # Conjoin the intervals by taking the outer boundary max
                    merged_intervals[-1] = (last_start, max(last_end, current_end))
                else:
                    merged_intervals.append((current_start, current_end))
            intervals = merged_intervals
        else:
            intervals = raw_intervals

        # --- Build Persistent Episodes from Intervals ---
        episodes = []
        for start_idx, end_idx in intervals:
            window_frames = frames[start_idx : end_idx + 1]
            if not window_frames:
                continue

            # --- Responsibility 6: Select Peak Frame ---
            # Locate the frame with the absolute highest significance within this consolidated window
            peak_frame = max(window_frames, key=lambda f: f.significance)
            peak_snap = peak_frame.snapshot

            first_snap = window_frames[0].snapshot
            last_snap = window_frames[-1].snapshot

            # --- Responsibility 7: Compute Summary Values ---
            max_fear = max(f.snapshot.fear for f in window_frames)
            avg_fear = sum(f.snapshot.fear for f in window_frames) / len(window_frames)

            max_stress = max(f.snapshot.stress for f in window_frames)
            avg_stress = sum(f.snapshot.stress for f in window_frames) / len(window_frames)

            max_drive = max(f.snapshot.drive for f in window_frames)
            avg_drive = sum(f.snapshot.drive for f in window_frames) / len(window_frames)

            # Physiological state tracking via net changes across the interval boundary
            energy_delta = last_snap.energy - first_snap.energy
            integrity_delta = last_snap.integrity - first_snap.integrity

            # --- Responsibility 8: Preserve Full Trace ---
            episode = EpisodicEvent(
                start_tick=first_snap.tick,
                peak_tick=peak_snap.tick,
                end_tick=last_snap.tick,
                event_type=peak_frame.event_type,
                peak_significance=peak_frame.significance,
                start_x=first_snap.pos_x,
                start_y=first_snap.pos_y,
                peak_x=peak_snap.pos_x,
                peak_y=peak_snap.pos_y,
                end_x=last_snap.pos_x,
                end_y=last_snap.pos_y,
                max_fear=max_fear,
                avg_fear=avg_fear,
                max_stress=max_stress,
                avg_stress=avg_stress,
                max_drive=max_drive,
                avg_drive=avg_drive,
                energy_delta=energy_delta,
                integrity_delta=integrity_delta,
                peak_snapshot=peak_snap,
                frame_trace=list(window_frames)  # Full uncompressed structural preservation
            )
            episodes.append(episode)

        return episodes
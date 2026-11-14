from typing import List, Dict
from ..schemas import EpisodeFrame
from .config import EpisodeBuilderConfig


class WindowExtractor:
    """Manages window slicing, pre-peak anticipation lookback, and post-peak idle tapering for episode intervals."""

    def __init__(self, config: EpisodeBuilderConfig):
        self.config = config

    def extract_asymmetric_window(
        self,
        interval,
        sorted_ticks: List[int],
        frame_map: Dict[int, EpisodeFrame],
        prev_end_tick: int,
        min_available_tick: int,
    ) -> List[EpisodeFrame]:
        """Computes dynamic asymmetric frame boundaries around an interval accounting for pre-peak runway and trailing taper."""
        prelim_frames = [
            frame_map[t]
            for t in sorted_ticks
            if interval.start_tick <= t <= interval.end_tick
        ]
        if not prelim_frames:
            return []

        peak_frame = max(prelim_frames, key=lambda f: f.importance)
        peak_tick = peak_frame.snapshot.tick

        expanded_start_tick = interval.start_tick
        for f in reversed(sorted_ticks):
            if f >= interval.start_tick:
                continue
            if f < prev_end_tick or f < min_available_tick:
                break
            frame_obj = frame_map[f]
            if (
                frame_obj.snapshot.stress > 0.15
                or frame_obj.snapshot.fear > 0.15
                or frame_obj.prediction_error > 0.8
                or frame_obj.attention_score > 0.3
            ):
                expanded_start_tick = f
            else:
                break

        min_runway_ticks = int((peak_tick - interval.start_tick) * 0.5)
        fallback_start = max(
            interval.start_tick - max(25, min_runway_ticks),
            prev_end_tick,
            min_available_tick,
        )
        expanded_start_tick = min(expanded_start_tick, fallback_start)

        trimmed_end_tick = interval.end_tick
        for f in reversed(prelim_frames):
            if f.snapshot.tick <= peak_frame.snapshot.tick:
                break
            if f.attention_score < 0.2 and f.importance < 0.3:
                trimmed_end_tick = f.snapshot.tick
            else:
                break

        return [
            frame_map[t]
            for t in sorted_ticks
            if expanded_start_tick <= t <= trimmed_end_tick
        ]

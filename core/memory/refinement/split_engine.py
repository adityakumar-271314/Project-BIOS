from typing import List, Optional
from ..schemas import EpisodicEvent, EpisodeFrame
from ..episode_builder import EpisodeBuilder
from ..boundary.boundary import BoundaryInterval


class SplitEngine:
    """
    Evaluates EpisodicEvent instances to detect internal behavioral shifts,
    finding natural cognitive troughs and rebuilding sub-events via EpisodeBuilder.
    """

    def __init__(
        self,
        min_split_duration: int = 40,
        search_radius: int = 12,
        episode_builder: Optional[EpisodeBuilder] = None,
    ):
        self.min_split_duration = min_split_duration
        self.search_radius = search_radius
        self.builder = episode_builder or EpisodeBuilder()

    def evaluate_splits(
        self,
        event: EpisodicEvent,
        frames: Optional[List[EpisodeFrame]] = None,
    ) -> List[EpisodicEvent]:
        sig = event.signature

        raw_split_ticks = set()
        for t in sig.goal_transitions:
            raw_split_ticks.add(t.tick)
        for t in sig.skill_transitions:
            raw_split_ticks.add(t.tick)
        for t in sig.target_transitions:
            raw_split_ticks.add(t.tick)

        if not raw_split_ticks or not frames:
            return [event]

        event_frames = [
            f for f in frames
            if event.start_tick <= f.snapshot.tick <= event.end_tick
        ]
        if not event_frames:
            return [event]

        frame_map = {f.snapshot.tick: f for f in event_frames}
        sorted_frame_ticks = sorted(frame_map.keys())

        adjusted_split_ticks = set()
        for raw_tick in raw_split_ticks:
            neighborhood = [
                frame_map[t] for t in sorted_frame_ticks 
                if abs(t - raw_tick) <= self.search_radius
            ]
            if not neighborhood:
                continue

            trough_frame = min(
                neighborhood, 
                key=lambda f: (f.importance * 0.7) + (f.attention_score * 0.3)
            )
            adjusted_split_ticks.add(trough_frame.snapshot.tick)

        sorted_splits = sorted(list(adjusted_split_ticks))
        if not sorted_splits:
            return [event]

        sub_events: List[EpisodicEvent] = []
        current_window: List[EpisodeFrame] = []

        for f in event_frames:
            if (
                f.snapshot.tick in sorted_splits
                and len(current_window) >= self.min_split_duration
            ):
                built = self._build_sub_episode(current_window)
                if built:
                    sub_events.extend(built)
                current_window = [f]
            else:
                current_window.append(f)

        if len(current_window) >= self.min_split_duration:
            built = self._build_sub_episode(current_window)
            if built:
                sub_events.extend(built)

        return sub_events if sub_events else [event]

    def _build_sub_episode(self, window_frames: List[EpisodeFrame]) -> List[EpisodicEvent]:
        """Forces EpisodeBuilder to process the sub-window using a synthetic boundary interval."""
        if not window_frames:
            return []
        synthetic_interval = BoundaryInterval(
            start_tick=window_frames[0].snapshot.tick,
            end_tick=window_frames[-1].snapshot.tick,
            start_confidence=1.0,
            end_confidence=1.0,
            start_reasons=["split_rebuild"],
            end_reasons=["split_rebuild"]
        )
        return self.builder.build(window_frames, boundaries=[synthetic_interval])
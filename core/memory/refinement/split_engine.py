from typing import List, Optional
from ..schemas import EpisodicEvent, EpisodeFrame
from ..episode_builder import EpisodeBuilder


class SplitEngine:
    """
    Evaluates EpisodicEvent instances to detect internal behavioral shifts or
    discontinuities, splitting them into multiple fine-grained EpisodicEvents.
    """

    def __init__(
        self,
        min_split_duration: int = 10,
        episode_builder: Optional[EpisodeBuilder] = None,
    ):
        self.min_split_duration = min_split_duration
        self.builder = episode_builder or EpisodeBuilder()

    def evaluate_splits(
        self,
        event: EpisodicEvent,
        frames: Optional[List[EpisodeFrame]] = None,
    ) -> List[EpisodicEvent]:
        """
        Evaluates a single EpisodicEvent. If internal transition flags or signature
        transitions reveal mid-episode behavioral switches, splits the event.
        """
        sig = event.signature

        # 1. Check for internal state shifts in signature
        has_goal_trans = len(sig.goal_transitions) > 0
        has_skill_trans = len(sig.skill_transitions) > 0
        has_target_trans = len(sig.target_transitions) > 0

        # If no internal transitions, return event unmodified
        if not (has_goal_trans or has_skill_trans or has_target_trans):
            return [event]

        # 2. Collect split ticks
        split_ticks = set()
        for t in sig.goal_transitions:
            split_ticks.add(t.tick)
        for t in sig.skill_transitions:
            split_ticks.add(t.tick)
        for t in sig.target_transitions:
            split_ticks.add(t.tick)

        sorted_splits = sorted(split_ticks)

        # 3. If raw frames are available, perform precise frame-level splitting
        if frames:
            event_frames = [
                f
                for f in frames
                if event.start_tick <= f.snapshot.tick <= event.end_tick
            ]
            if not event_frames:
                return [event]

            sub_events: List[EpisodicEvent] = []
            current_window: List[EpisodeFrame] = []

            for f in event_frames:
                if (
                    f.snapshot.tick in sorted_splits
                    and len(current_window) >= self.min_split_duration
                ):
                    built = self.builder.build(current_window)
                    if built:
                        sub_events.extend(built)
                    current_window = [f]
                else:
                    current_window.append(f)

            if len(current_window) >= self.min_split_duration:
                built = self.builder.build(current_window)
                if built:
                    sub_events.extend(built)

            return sub_events if sub_events else [event]

        # Fallback: If no raw frame context is available, preserve the original event
        return [event]

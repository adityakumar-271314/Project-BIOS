import math
from typing import List, Optional, Set, Dict, Any
from ..schemas import EpisodicEvent, EpisodeFrame
from ..episode_builder import EpisodeBuilder
from ..boundary.boundary import BoundaryInterval
from .dynamic_profiler import AdaptiveParameterManager, AdaptiveParameters


class SplitEngine:
    """
    Evaluates EpisodicEvent instances to detect internal behavioral shifts,
    finding natural cognitive troughs using adaptive search radii and entropy-driven
    duration quotas, then rebuilding sub-events via EpisodeBuilder.
    """

    def __init__(
        self,
        parameter_manager: Optional[AdaptiveParameterManager] = None,
        episode_builder: Optional[EpisodeBuilder] = None,
    ):
        self.param_manager = parameter_manager or AdaptiveParameterManager()
        self.builder = episode_builder or EpisodeBuilder()

    def evaluate_splits(
        self,
        event: EpisodicEvent,
        frames: Optional[List[EpisodeFrame]] = None,
        override_params: Optional[AdaptiveParameters] = None,
    ) -> List[EpisodicEvent]:
        """
        Evaluates an episode for internal behavioral splits using dynamic parameters
        derived from event metrics and rolling statistical baselines.
        """
        sig = event.signature

        # Extract raw transition ticks
        raw_split_ticks: Set[int] = set()
        for t in sig.goal_transitions:
            raw_split_ticks.add(t.tick)
        for t in sig.skill_transitions:
            raw_split_ticks.add(t.tick)
        for t in sig.target_transitions:
            raw_split_ticks.add(t.tick)

        if not raw_split_ticks or not frames:
            return [event]

        # Get relevant frame window
        event_frames = [
            f for f in frames if event.start_tick <= f.snapshot.tick <= event.end_tick
        ]
        if not event_frames:
            return [event]

        # Compute dynamic parameters for this specific evaluation pass
        current_velocity = self._compute_mean_velocity(event_frames)
        params = override_params or self.param_manager.get_adaptive_parameters(
            current_complexity=sig.behavioral_complexity,
            current_velocity=current_velocity,
        )

        frame_map = {f.snapshot.tick: f for f in event_frames}
        sorted_frame_ticks = sorted(frame_map.keys())

        # Step 1: Adaptive Trough Finding within Dynamic Search Radius
        adjusted_split_ticks: Set[int] = set()
        for raw_tick in raw_split_ticks:
            neighborhood = [
                frame_map[t]
                for t in sorted_frame_ticks
                if abs(t - raw_tick) <= params.search_radius
            ]
            if not neighborhood:
                continue

            # Find cognitive trough using dynamic arousal/attention weighting
            trough_frame = min(
                neighborhood,
                key=lambda f: self._compute_trough_score(f),
            )
            adjusted_split_ticks.add(trough_frame.snapshot.tick)

        sorted_splits = sorted(list(adjusted_split_ticks))
        if not sorted_splits:
            return [event]

        # Step 2: Slice Window & Enforce Dynamic Entropy-Driven Duration Quota
        sub_events: List[EpisodicEvent] = []
        current_window: List[EpisodeFrame] = []

        for f in event_frames:
            if (
                f.snapshot.tick in sorted_splits
                and len(current_window) >= params.min_split_duration
            ):
                built = self._build_sub_episode(current_window)
                if built:
                    sub_events.extend(built)
                current_window = [f]
            else:
                current_window.append(f)

        if len(current_window) >= params.min_split_duration:
            built = self._build_sub_episode(current_window)
            if built:
                sub_events.extend(built)

        return sub_events if sub_events else [event]

    def _compute_trough_score(self, frame: EpisodeFrame) -> float:
        """
        Computes a dynamic score to identify cognitive troughs. Lower values indicate
        deeper troughs suitable for clean behavioral boundary placement.
        """
        # Dynamic weighting based on current frame arousal/stress
        arousal = max(frame.snapshot.stress, frame.snapshot.fear)
        
        # During high arousal, prediction error and attention are weighted higher to avoid splitting mid-reaction
        importance_weight = 0.7 - (0.2 * arousal)
        attention_weight = 0.3 + (0.2 * arousal)

        return (frame.importance * importance_weight) + (frame.attention_score * attention_weight)

    def _compute_mean_velocity(self, frames: List[EpisodeFrame]) -> float:
        """Calculates average spatial velocity across the frame sequence."""
        if not frames:
            return 0.0
        total_vel = sum(
            math.hypot(f.snapshot.vel_x, f.snapshot.vel_y) for f in frames
        )
        return total_vel / len(frames)

    def _build_sub_episode(
        self, window_frames: List[EpisodeFrame]
    ) -> List[EpisodicEvent]:
        """Forces EpisodeBuilder to process the sub-window using a synthetic boundary interval."""
        if not window_frames:
            return []
        synthetic_interval = BoundaryInterval(
            start_tick=window_frames[0].snapshot.tick,
            end_tick=window_frames[-1].snapshot.tick,
            start_confidence=1.0,
            end_confidence=1.0,
            start_reasons=["adaptive_split_rebuild"],
            end_reasons=["adaptive_split_rebuild"],
        )
        return self.builder.build(window_frames, boundaries=[synthetic_interval])
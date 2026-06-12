from __future__ import annotations
from collections import deque
from typing import Any, List, Tuple

from .schemas import EpisodeFrame, TickSnapshot


class TemporalBuffer:
    """Short-term autobiographical stream.

    Holds recent high-fidelity agent state for future episode reconstruction.

    This is NOT memory. It is a transient rolling window.
    """

    def __init__(self, seconds: int = 15, fps: int = 60) -> None:
        self.seconds = seconds
        self.fps = fps
        self.maxlen = seconds * fps

        self._snapshots: deque[TickSnapshot] = deque(maxlen=self.maxlen)
        self._frames: deque[EpisodeFrame] = deque(maxlen=self.maxlen)

    def append_snapshot(self, snapshot: TickSnapshot) -> None:
        self._snapshots.append(snapshot)

    def append_frame(self, frame: EpisodeFrame) -> None:
        self._frames.append(frame)

    def clear(self) -> None:
        self._snapshots.clear()
        self._frames.clear()

    def latest(self) -> TickSnapshot | None:
        return self._snapshots[-1] if self._snapshots else None

    def latest_frame(self) -> EpisodeFrame | None:
        return self._frames[-1] if self._frames else None

    def snapshots(self) -> Tuple[TickSnapshot, ...]:
        return tuple(self._snapshots)

    def frames(self) -> Tuple[EpisodeFrame, ...]:
        return tuple(self._frames)

    def __len__(self) -> int:
        return len(self._snapshots)

    def get_range(self, start_tick: int, end_tick: int) -> List[TickSnapshot]:
        return [
            snap for snap in self._snapshots if start_tick <= snap.tick <= end_tick
        ]

    def find_tick(self, tick: int) -> TickSnapshot | None:
        for snap in self._snapshots:
            if snap.tick == tick:
                return snap
        return None

    def recent_seconds(self, seconds: float) -> Tuple[TickSnapshot, ...]:
        ticks = int(seconds * self.fps)
        if ticks <= 0:
            return ()
        # Slice from the end of the deque efficiently
        return tuple(list(self._snapshots)[-ticks:])

    def get_context(
        self, center_tick: int, before_ticks: int, after_ticks: int
    ) -> List[TickSnapshot]:
        return self.get_range(
            start_tick=center_tick - before_ticks,
            end_tick=center_tick + after_ticks,
        )

    def get_before(self, tick: int, ticks: int) -> List[TickSnapshot]:
        return self.get_range(tick - ticks, tick)

    def get_after(self, tick: int, ticks: int) -> List[TickSnapshot]:
        return self.get_range(tick, tick + ticks)

    def context_for_event(
        self, event_tick: int, retrospective_ticks: int
    ) -> List[TickSnapshot]:
        return self.get_context(
            center_tick=event_tick,
            before_ticks=retrospective_ticks,
            after_ticks=0,
        )

    def get_frame_context(
        self, center_tick: int, before_ticks: int, after_ticks: int
    ) -> List[EpisodeFrame]:
        """Slices historical frames within a temporal bounding window around an attention target."""
        start_tick = center_tick - before_ticks
        end_tick = center_tick + after_ticks
        return [
            frame for frame in self._frames if start_tick <= frame.snapshot.tick <= end_tick
        ]

    def capture(
        self,
        *,
        tick: int,
        sensors: Any,
        body: Any,
        emotions: Any,
        semantic_memory: Any,
        goal: Any,
        active_skill: Any,
        target: Any,
    ) -> None:
        snapshot = TickSnapshot(
            tick=tick,
            # spatial
            pos_x=semantic_memory.position.x,
            pos_y=semantic_memory.position.y,
            vel_x=semantic_memory.velocity.x,
            vel_y=semantic_memory.velocity.y,
            heading=semantic_memory.internal_heading,
            # body
            energy=body.energy,
            integrity=body.integrity,
            # emotions
            stress=emotions.stress,
            fear=emotions.fear,
            drive=emotions.drive,
            # goal state
            goal_name=getattr(goal, "name"),
            goal_priority=getattr(goal, "priority", 0.0),
            # execution state
            active_skill=active_skill,
            # target state
            target_type=getattr(target, "type", None),
            target_id=getattr(target, "id", None),
            target_x=getattr(target, "x", None),
            target_y=getattr(target, "y", None),
            # environment summary
            visible_food=sum(1 for obj in sensors.sensed_objects if obj.type == "food"),
            visible_hazards=sum(1 for obj in sensors.sensed_objects if obj.type == "hazard"),
            visible_landmarks=sum(1 for obj in sensors.sensed_objects if obj.type == "landmark"),
            hazard_stim=sensors.hazard_stim,
            food_stim=sensors.food_stim,
        )

        self.append_snapshot(snapshot)
import math
from typing import List, Set
from ..schemas import EpisodicEvent, SparseFrame


class RedundancyPruner:
    """
    Evaluates candidate anchors and removes those that contribute no meaningful
    behavioral, spatial, or emotional information relative to their neighbors.

    Guarantees structural anchors (start, peak, end, signature transitions) are never pruned.
    Does NOT modify signatures, reorder frames, or use interpolation/reconstruction.
    """

    def __init__(
        self,
        pos_threshold: float = 0.5,
        heading_threshold: float = 0.25,  # radians (~14 degrees)
        vel_threshold: float = 0.2,
        resource_threshold: float = 0.05,
        emotion_threshold: float = 0.05,
    ):
        self.pos_threshold = pos_threshold
        self.heading_threshold = heading_threshold
        self.vel_threshold = vel_threshold
        self.resource_threshold = resource_threshold
        self.emotion_threshold = emotion_threshold

    def prune_anchors(
        self, anchors: List[SparseFrame], event: EpisodicEvent
    ) -> List[SparseFrame]:
        if len(anchors) <= 2:
            return list(anchors)

        # 1. Identify protected ticks (start, peak, end, signature transitions)
        protected_ticks: Set[int] = {
            event.start_tick,
            event.peak_tick,
            event.end_tick,
        }

        if event.signature:
            for trans in event.signature.goal_transitions:
                protected_ticks.add(trans.tick)
            for trans in event.signature.skill_transitions:
                protected_ticks.add(trans.tick)
            for trans in event.signature.target_transitions:
                protected_ticks.add(trans.tick)

        # 2. Sequential non-cascading pruning pass
        pruned_anchors = [anchors[0]]

        for i in range(1, len(anchors) - 1):
            curr = anchors[i]

            # Protected ticks are always kept
            if curr.tick in protected_ticks:
                pruned_anchors.append(curr)
                continue

            prev = pruned_anchors[-1]
            next_f = anchors[i + 1]

            # If removing 'curr' introduces significant deviation between 'prev' and 'next_f', keep 'curr'
            if self._is_anchor_essential(prev, curr, next_f):
                pruned_anchors.append(curr)

        # Always keep the final anchor
        pruned_anchors.append(anchors[-1])
        return pruned_anchors

    def _is_anchor_essential(
        self, prev: SparseFrame, curr: SparseFrame, next_f: SparseFrame
    ) -> bool:
        # Behavioral state shifts relative to previous frame
        if (
            curr.active_skill != prev.active_skill
            or curr.action_state != prev.action_state
            or curr.target_type != prev.target_type
        ):
            return True

        # Sudden environmental presence
        if (curr.visible_food != prev.visible_food) or (
            curr.visible_hazards != prev.visible_hazards
        ):
            return True

        # Position change check (perpendicular distance to straight-line trajectory)
        if self._spatial_deviation(prev, curr, next_f) > self.pos_threshold:
            return True

        # Heading change check
        if abs(self._angle_diff(curr.heading, prev.heading)) > self.heading_threshold:
            return True

        # Velocity change check
        if (
            abs(curr.vel_x - prev.vel_x) > self.vel_threshold
            or abs(curr.vel_y - prev.vel_y) > self.vel_threshold
        ):
            return True

        # Resource changes (energy, integrity)
        if (
            abs(curr.energy - prev.energy) > self.resource_threshold
            or abs(curr.integrity - prev.integrity) > self.resource_threshold
        ):
            return True

        # Emotional changes (stress, fear, drive)
        if (
            abs(curr.stress - prev.stress) > self.emotion_threshold
            or abs(curr.fear - prev.fear) > self.emotion_threshold
            or abs(curr.drive - prev.drive) > self.emotion_threshold
        ):
            return True

        return False

    @staticmethod
    def _spatial_deviation(
        prev: SparseFrame, curr: SparseFrame, next_f: SparseFrame
    ) -> float:
        """Calculates perpendicular distance from curr to the line segment (prev -> next_f)."""
        dx = next_f.pos_x - prev.pos_x
        dy = next_f.pos_y - prev.pos_y
        length_sq = dx * dx + dy * dy

        if length_sq == 0:
            return math.hypot(curr.pos_x - prev.pos_x, curr.pos_y - prev.pos_y)

        # Projection factor
        t = max(
            0.0,
            min(
                1.0,
                ((curr.pos_x - prev.pos_x) * dx + (curr.pos_y - prev.pos_y) * dy)
                / length_sq,
            ),
        )

        proj_x = prev.pos_x + t * dx
        proj_y = prev.pos_y + t * dy

        return math.hypot(curr.pos_x - proj_x, curr.pos_y - proj_y)

    @staticmethod
    def _angle_diff(a1: float, a2: float) -> float:
        """Calculates the shortest angular difference in radians."""
        diff = (a1 - a2) % (2 * math.pi)
        if diff > math.pi:
            diff -= 2 * math.pi
        return diff

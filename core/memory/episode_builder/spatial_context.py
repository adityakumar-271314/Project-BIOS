import math
from typing import Tuple
from ..schemas import EpisodeFrame, SpatialContextReference, SpatialEntityType
from .config import EpisodeBuilderConfig


class SpatialContextExtractor:
    """Extracts and filters salient spatial context references (landmarks, hazards, and food patches) around keyframes."""

    def __init__(self, config: EpisodeBuilderConfig):
        self.config = config

    def extract(self, frame: EpisodeFrame) -> Tuple[SpatialContextReference, ...]:
        """Returns a tuple of filtered and prioritized spatial context references within the configured capture radius."""
        contexts = []
        snap = frame.snapshot
        agent_x, agent_y = snap.pos_x, snap.pos_y

        if snap.target_type == "landmark" and snap.target_id is not None:
            dx = (snap.target_x if snap.target_x is not None else agent_x) - agent_x
            dy = (snap.target_y if snap.target_y is not None else agent_y) - agent_y
            dist = math.hypot(dx, dy)
            if dist <= self.config.max_capture_radius:
                contexts.append(
                    SpatialContextReference(
                        entity_type=SpatialEntityType.LANDMARK,
                        entity_id=snap.target_id,
                        pos_x=snap.target_x if snap.target_x is not None else agent_x,
                        pos_y=snap.target_y if snap.target_y is not None else agent_y,
                        intensity=1.0,
                    )
                )

        if snap.hazard_stim > 0.2:
            contexts.append(
                SpatialContextReference(
                    entity_type=SpatialEntityType.HAZARD_ZONE,
                    entity_id=None,
                    pos_x=agent_x,
                    pos_y=agent_y,
                    intensity=snap.hazard_stim,
                )
            )
        if snap.food_stim > 0.2:
            contexts.append(
                SpatialContextReference(
                    entity_type=SpatialEntityType.FOOD_PATCH,
                    entity_id=None,
                    pos_x=agent_x,
                    pos_y=agent_y,
                    intensity=snap.food_stim,
                )
            )

        unique_contexts = {}
        for c in contexts:
            key = (c.entity_type, c.entity_id, round(c.pos_x, 1), round(c.pos_y, 1))
            if (
                key not in unique_contexts
                or c.intensity > unique_contexts[key].intensity
            ):
                unique_contexts[key] = c

        sorted_contexts = sorted(
            unique_contexts.values(), key=lambda x: x.intensity, reverse=True
        )
        return tuple(sorted_contexts[:3])

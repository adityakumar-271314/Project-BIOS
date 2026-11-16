from __future__ import annotations
from typing import Optional
from ..schemas import EpisodicEvent, HierarchyLevel, HierarchyGraphState
from .config import HierarchyConfig
from .aggregator import SummaryAggregator

class HierarchyManager:
    """
    Manages true multi-episode clustering (Group -> Mission -> Narrative) without
    bloating indices with redundant 1:1 leaf episode nodes[cite: 1].
    """
    def __init__(self, config: Optional[HierarchyConfig] = None):
        self.config = config or HierarchyConfig()
        self.graph_state = HierarchyGraphState()
        self._active_group_id: Optional[str] = None

    def add_episode(self, event: EpisodicEvent, episode_id_str: str, quality_score: float = 1.0, importance_score: float = 0.0) -> None:
        """
        Conditionally clusters the incoming episode into the active group or spawns a new group 
        only when contextual boundaries shift.
        """
        active_group = self.graph_state.hierarchies.get(self._active_group_id) if self._active_group_id else None
        
        should_merge = False
        if active_group:
            sig = active_group.dominant_signature
            same_goal = (sig.dominant_goal is None or sig.dominant_goal == event.signature.dominant_goal)
            same_landmark = (sig.nearest_landmark_id is None or sig.nearest_landmark_id == event.signature.nearest_landmark_id)
            within_temporal_window = (event.start_tick - active_group.end_tick) <= self.config.max_group_temporal_gap
            
            if same_goal and (same_landmark or within_temporal_window):
                should_merge = True

        if should_merge and active_group:
            # Append episode reference to existing group and update span bounds
            updated_episode_ids = list(active_group.episode_ids) + [episode_id_str]
            updated_end_tick = max(active_group.end_tick, event.end_tick)
            updated_duration = updated_end_tick - active_group.start_tick + 1
            
            active_group.episode_ids = tuple(updated_episode_ids)
            active_group.end_tick = updated_end_tick
            active_group.duration_ticks = updated_duration
        else:
            # Spawn a new Group container only on contextual breaks
            group_id = f"group_{len(self.graph_state.hierarchies) + 1:04d}"
            new_group = SummaryAggregator.create_hierarchy_unit(
                hierarchy_id=group_id,
                level=HierarchyLevel.GROUP,
                root_id=group_id,
                events=[event],
                qualities=[quality_score],
                importances=[importance_score]
            )
            # Override episode_ids to use the clean string identifier (e.g. "episode_000001")
            new_group.episode_ids = (episode_id_str,)
            
            self.graph_state.hierarchies[group_id] = new_group
            self._active_group_id = group_id
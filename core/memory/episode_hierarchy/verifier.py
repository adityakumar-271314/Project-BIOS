from __future__ import annotations
from typing import Dict, Any, Optional, Tuple
from ..schemas import EpisodicEvent, EpisodeNode, HierarchyLevel
from .config import HierarchyConfig

class RelationshipVerifier:
    """
    Verifies and establishes explicit relational edges across the four core dimensions:
    temporal, spatial, behavioral, and causal[cite: 1].
    """
    def __init__(self, config: Optional[HierarchyConfig] = None):
        self.config = config or HierarchyConfig()

    def verify_temporal(self, prev_event: EpisodicEvent, curr_event: EpisodicEvent) -> Tuple[bool, int, int]:
        """Verifies monotonic start/end tick ordering[cite: 1]."""
        is_sequential = curr_event.start_tick >= prev_event.start_tick
        return is_sequential, prev_event.start_tick, curr_event.end_tick

    def verify_spatial(self, prev_event: EpisodicEvent, curr_event: EpisodicEvent) -> Tuple[bool, Optional[int]]:
        """Verifies shared landmark anchors and spatial continuity[cite: 1]."""
        prev_landmark = prev_event.signature.nearest_landmark_id
        curr_landmark = curr_event.signature.nearest_landmark_id
        
        shared_landmark = curr_landmark if (curr_landmark is not None and curr_landmark == prev_landmark) else None
        spatial_continuous = shared_landmark is not None or (
            abs(curr_event.start_x - prev_event.end_x) <= self.config.max_group_spatial_radius and
            abs(curr_event.start_y - prev_event.end_y) <= self.config.max_group_spatial_radius
        )
        return spatial_continuous, shared_landmark

    def verify_behavioral(self, prev_event: EpisodicEvent, curr_event: EpisodicEvent) -> bool:
        """Verifies dominant goal, skill, and target consistency[cite: 1]."""
        p_sig = prev_event.signature
        c_sig = curr_event.signature
        
        goal_match = (p_sig.dominant_goal is not None and p_sig.dominant_goal == c_sig.dominant_goal)
        skill_match = (p_sig.dominant_skill is not None and p_sig.dominant_skill == c_sig.dominant_skill)
        target_match = (p_sig.dominant_target is not None and p_sig.dominant_target == c_sig.dominant_target)
        
        matches = sum([goal_match, skill_match, target_match])
        return matches >= 1 or (not p_sig.dominant_goal and not c_sig.dominant_goal)

    def verify_causal(self, prev_event: EpisodicEvent, curr_event: EpisodicEvent) -> Optional[str]:
        """Detects cause-and-effect chains across episode boundaries[cite: 1]."""
        prev_sig = prev_event.signature
        curr_sig = curr_event.signature
        
        # Check integrity drop or hazard exposure followed by defensive/recovery transition
        prev_integrity_change = prev_sig.net_resource_deltas.get("integrity", 0.0)
        if prev_integrity_change <= self.config.causal_integrity_drop_threshold or prev_sig.max_hazard_exposure > self.config.causal_hazard_exposure_threshold:
            if curr_sig.dominant_skill in ("retreat", "heal", "evade", "flee") or "hazard_exposure" in curr_sig.primary_importance_drivers:
                return "causal"
        
        if prev_sig.nearest_landmark_id is not None and prev_sig.nearest_landmark_id == curr_sig.nearest_landmark_id:
            return "spatial_continuation"
            
        return None
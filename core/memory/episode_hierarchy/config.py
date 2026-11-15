from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass(slots=True)
class HierarchyConfig:
    """
    Adaptive configuration parameters and thresholds for multi-tier hierarchical
    memory clustering, relationship verification, and retrieval[cite: 1].
    """
    # Group Formation Thresholds
    max_group_spatial_radius: float = 150.0  # Max distance between consecutive episodes to cluster into a Group[cite: 1]
    max_group_temporal_gap: int = 300       # Max tick gap allowed within a local Group
    behavioral_continuity_match: float = 0.6 # Minimum signature overlap to maintain Group continuity

    # Mission Formation Thresholds
    max_mission_duration_ticks: int = 10000
    mission_spatial_transition_threshold: float = 200.0

    # Causal & Hazard Detection Thresholds
    causal_integrity_drop_threshold: float = -0.1
    causal_hazard_exposure_threshold: float = 0.3

    # Retrieval Defaults
    default_top_k_candidates: int = 5
    quality_weight: float = 0.4
    importance_weight: float = 0.6
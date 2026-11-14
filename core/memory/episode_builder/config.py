from dataclasses import dataclass, field
from typing import Dict


@dataclass
class EpisodeBuilderConfig:
    """Centralized configuration settings, weights, and operational thresholds for the EpisodeBuilder pipeline."""

    compression_ratio: float = 0.03
    min_keyframes: int = 3
    change_threshold: float = 0.25
    pre_peak_runway_ticks: int = 50
    max_capture_radius: float = 150.0
    trajectory_threshold_rad: float = 0.35
    anchor_tier_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "boundary": 1.0,
            "event_critical": 0.85,
            "state_critical": 0.70,
            "trajectory_critical": 0.50,
        }
    )
    suppression_penalty_factor: float = 0.65
    min_sigma_ticks: float = 2.0

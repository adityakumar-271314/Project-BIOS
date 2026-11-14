import math
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

class RunningStats:
    """Tracks running mean, variance, and standard deviation for streaming telemetry."""
    def __init__(self):
        self.n = 0
        self.mean = 0.0
        self._M2 = 0.0

    def update(self, value: float):
        self.n += 1
        delta = value - self.mean
        self.mean += delta / self.n
        delta2 = value - self.mean
        self._M2 += delta * delta2

    @property
    def variance(self) -> float:
        return self._M2 / (self.n - 1) if self.n > 1 else 0.0

    @property
    def std(self) -> float:
        return math.sqrt(self.variance)


@dataclass(slots=True)
class AdaptiveParameters:
    """Container for current dynamic operational parameters."""
    search_radius: int
    min_split_duration: int
    interruption_hazard_thresh: float
    interruption_integrity_drop: float
    max_keyframe_percentage: float
    base_similarity_threshold: float


class AdaptiveParameterManager:
    """
    Maintains rolling statistical baselines of agent telemetry and computes
    context-aware, adaptive thresholds for the Split/Merge refinement pipeline.
    """

    def __init__(
        self,
        window_capacity: int = 100,
        default_hazard_thresh: float = 0.60,
        default_integrity_drop: float = 0.20,
    ):
        self.window_capacity = window_capacity
        self.default_hazard_thresh = default_hazard_thresh
        self.default_integrity_drop = default_integrity_drop

        # Telemetry rolling trackers using RunningStats
        self.stats: Dict[str, RunningStats] = {
            "duration": RunningStats(),
            "hazard_exposure": RunningStats(),
            "integrity_delta": RunningStats(),
            "behavioral_complexity": RunningStats(),
            "velocity": RunningStats(),
        }

    def observe_event(self, event_metrics: Dict[str, float]):
        """Ingests metrics from newly processed events to update rolling baselines."""
        for key, value in event_metrics.items():
            if key in self.stats:
                self.stats[key].update(value)

    def get_adaptive_parameters(
        self, 
        current_complexity: float = 0.5,
        current_velocity: float = 0.0
    ) -> AdaptiveParameters:
        """
        Computes dynamic operational parameters scaled to current behavioral tempo
        and historical statistical baselines.
        """
        # 1. Adaptive Search Radius (scales with velocity and complexity)
        base_radius = 12
        vel_std = self.stats["velocity"].std or 1.0
        vel_factor = min(2.0, max(0.5, current_velocity / vel_std))
        dynamic_radius = int(base_radius * vel_factor * (1.0 + 0.5 * current_complexity))
        search_radius = max(6, min(30, dynamic_radius))

        # 2. Adaptive Minimum Split Duration (proportional to historical event duration mean)
        mean_duration = self.stats["duration"].mean
        if mean_duration > 0:
            min_split_duration = max(20, int(mean_duration * 0.15))
        else:
            min_split_duration = 40  # Fallback baseline

        # 3. Z-Score / Percentile-Based Interruption Thresholds for Hazards
        hazard_mean = self.stats["hazard_exposure"].mean
        hazard_std = self.stats["hazard_exposure"].std
        if self.stats["hazard_exposure"].n > 5:
            # Trigger interruption if hazard exceeds mean + 1.5 standard deviations
            adaptive_hazard_thresh = hazard_mean + (1.5 * hazard_std)
            interruption_hazard_thresh = max(0.3, min(0.85, adaptive_hazard_thresh))
        else:
            interruption_hazard_thresh = self.default_hazard_thresh

        # 4. Integrity Discontinuity Drop Threshold
        integrity_mean = abs(self.stats["integrity_delta"].mean)
        integrity_std = self.stats["integrity_delta"].std
        if self.stats["integrity_delta"].n > 5:
            adaptive_integrity_drop = integrity_mean + (2.0 * integrity_std)
            interruption_integrity_drop = max(0.1, min(0.50, adaptive_integrity_drop))
        else:
            interruption_integrity_drop = self.default_integrity_drop

        # 5. Dynamic Keyframe Percentage (scales inversely with information complexity)
        # More complex events get a higher percentage budget, simple ones get lean budgeting
        comp_mean = self.stats["behavioral_complexity"].mean or 0.5
        complexity_ratio = min(1.0, max(0.2, current_complexity / max(0.1, comp_mean)))
        max_keyframe_percentage = 0.05 + (0.15 * complexity_ratio)

        # 6. Base Similarity Threshold
        base_similarity_threshold = 0.70

        return AdaptiveParameters(
            search_radius=search_radius,
            min_split_duration=min_split_duration,
            interruption_hazard_thresh=interruption_hazard_thresh,
            interruption_integrity_drop=interruption_integrity_drop,
            max_keyframe_percentage=max_keyframe_percentage,
            base_similarity_threshold=base_similarity_threshold,
        )
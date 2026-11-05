import math
from typing import Dict, Optional
from ..schemas import EpisodeSignature, StateSummary
from .dynamic_profiler import AdaptiveParameterManager, AdaptiveParameters


class SignatureSimilarityEvaluator:
    """
    Computes behavioral similarity and detects semantic interruptions
    between adjacent EpisodeSignature instances using dynamic statistical thresholds.
    """

    def __init__(
        self,
        parameter_manager: Optional[AdaptiveParameterManager] = None,
        goal_weight: float = 0.35,
        skill_weight: float = 0.25,
        target_weight: float = 0.20,
        resource_weight: float = 0.10,
        emotion_weight: float = 0.10,
    ):
        self.param_manager = parameter_manager or AdaptiveParameterManager()
        self.goal_weight = goal_weight
        self.skill_weight = skill_weight
        self.target_weight = target_weight
        self.resource_weight = resource_weight
        self.emotion_weight = emotion_weight

    def check_interruption(
        self, 
        sig_a: EpisodeSignature, 
        sig_b: EpisodeSignature,
        override_params: Optional[AdaptiveParameters] = None
    ) -> bool:
        """
        Determines whether a genuine semantic interruption occurred between two episodes
        using dynamic rolling thresholds for hazards and resource integrity drops.
        """
        params = override_params or self.param_manager.get_adaptive_parameters(
            current_complexity=max(sig_a.behavioral_complexity, sig_b.behavioral_complexity)
        )

        # 1. Dynamic Hazard Exposure / Threat Spikes (Z-Score derived)
        if (
            sig_a.max_hazard_exposure > params.interruption_hazard_thresh
            or sig_b.max_hazard_exposure > params.interruption_hazard_thresh
        ):
            return True

        # 2. Dynamic Major Integrity Discontinuity (e.g., severe damage / combat)
        integrity_a = sig_a.resource_summaries.get("integrity")
        integrity_b = sig_b.resource_summaries.get("integrity")
        if integrity_a and integrity_b:
            if (
                abs(integrity_a.net_change) > params.interruption_integrity_drop
                or abs(integrity_b.net_change) > params.interruption_integrity_drop
            ):
                return True

        # 3. Explicit Behavioral Shift Drivers
        if (
            "hazard_exposure" in sig_b.primary_importance_drivers
            or "integrity_change" in sig_b.primary_importance_drivers
        ):
            return True

        # 4. Abrupt Dominant Goal Replacement (when both are explicitly set)
        if (
            sig_a.dominant_goal
            and sig_b.dominant_goal
            and sig_a.dominant_goal != sig_b.dominant_goal
        ):
            return True

        return False

    def compute_similarity(
        self, sig_a: EpisodeSignature, sig_b: EpisodeSignature
    ) -> float:
        """
        Computes a normalized similarity score in range [0.0, 1.0] across behavioral
        identities and continuous metric bounds.
        """
        goal_sim = self._categorical_sim(sig_a.dominant_goal, sig_b.dominant_goal)
        skill_sim = self._categorical_sim(sig_a.dominant_skill, sig_b.dominant_skill)
        target_sim = self._categorical_sim(sig_a.dominant_target, sig_b.dominant_target)

        resource_sim = self._compare_summaries(
            sig_a.resource_summaries, sig_b.resource_summaries
        )
        emotion_sim = self._compare_summaries(
            sig_a.emotion_summaries, sig_b.emotion_summaries
        )

        total_score = (
            self.goal_weight * goal_sim
            + self.skill_weight * skill_sim
            + self.target_weight * target_sim
            + self.resource_weight * resource_sim
            + self.emotion_weight * emotion_sim
        )

        return max(0.0, min(1.0, total_score))

    def _categorical_sim(self, val_a: Optional[str], val_b: Optional[str]) -> float:
        if val_a is None and val_b is None:
            return 1.0
        if val_a is None or val_b is None:
            return 0.5
        return 1.0 if val_a == val_b else 0.0

    def _compare_summaries(
        self,
        summaries_a: Dict[str, StateSummary],
        summaries_b: Dict[str, StateSummary],
    ) -> float:
        keys = set(summaries_a.keys()).intersection(summaries_b.keys())
        if not keys:
            return 1.0

        sim_sum = 0.0
        for k in keys:
            sa, sb = summaries_a[k], summaries_b[k]
            boundary_diff = abs(sa.final - sb.initial)
            scale = max(1.0, abs(sa.max_val - sa.min_val), abs(sb.max_val - sb.min_val))
            sim_sum += math.exp(-2.0 * (boundary_diff / scale))

        return sim_sum / len(keys)
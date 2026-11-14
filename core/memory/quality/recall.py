from typing import Tuple, List
from ..schemas import EpisodicEvent, OutcomeStatus


class RecallUsefulnessEvaluator:
    """
    Estimates future recall usefulness based on explicit outcome status,
    landmark anchoring, environmental exposure, and coherence.
    """

    def evaluate(
        self,
        event: EpisodicEvent,
        coherence_score: float,
    ) -> Tuple[float, List[str]]:
        reasons = []
        sig = event.signature

        identity_score = 0.0
        if sig.dominant_goal:
            identity_score += 0.35
        if sig.dominant_skill:
            identity_score += 0.25
        if sig.outcome_status in (OutcomeStatus.COMPLETED, OutcomeStatus.INTERRUPTED):
            identity_score += 0.40
            reasons.append(f"resolved_outcome_{sig.outcome_status.value}")

        interaction_score = 0.0
        if sig.landmark_interactions > 0 or sig.nearest_landmark_id is not None:
            interaction_score += 0.3
            reasons.append("spatial_landmark_anchoring")
        if sig.max_reward_exposure > 0.5 or sig.max_hazard_exposure > 0.5:
            interaction_score += 0.4
            reasons.append("significant_environmental_exposure")
        if event.peak_significance > 0.6:
            interaction_score += 0.3

        interaction_score = min(1.0, interaction_score)
        raw_usefulness = (0.5 * identity_score) + (0.5 * interaction_score)
        recall_score = raw_usefulness * (0.5 + 0.5 * coherence_score)

        return round(min(1.0, max(0.0, recall_score)), 4), reasons

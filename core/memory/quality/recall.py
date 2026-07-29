from typing import Tuple, List
from ..schemas import EpisodicEvent


class RecallUsefulnessEvaluator:
    """
    Estimates how useful this episode will be for future memory recall queries.
    High usefulness comes from clear goals, explicit outcomes, landmark interactions,
    and high coherence.
    """

    def evaluate(
        self,
        event: EpisodicEvent,
        coherence_score: float,
    ) -> Tuple[float, List[str]]:
        reasons = []
        sig = event.signature

        # 1. Clear Outcome & Behavioral Identity
        identity_score = 0.0
        if sig.dominant_goal:
            identity_score += 0.35
        if sig.dominant_skill:
            identity_score += 0.25
        if sig.outcome_completed:
            identity_score += 0.40
            reasons.append("completed_goal_outcome")

        # 2. Environment Interaction & Impact
        interaction_score = 0.0
        if sig.landmark_interactions > 0:
            interaction_score += 0.3
            reasons.append("landmark_interaction")
        if sig.max_reward_exposure > 0.5 or sig.max_hazard_exposure > 0.5:
            interaction_score += 0.4
            reasons.append("significant_environmental_exposure")
        if event.peak_significance > 0.6:
            interaction_score += 0.3

        interaction_score = min(1.0, interaction_score)

        # 3. Composite Recall Usefulness Score (Gated by coherence)
        raw_usefulness = (0.5 * identity_score) + (0.5 * interaction_score)

        # Incoherent episodes are hard to retrieve usefully
        recall_score = raw_usefulness * (0.5 + 0.5 * coherence_score)

        return round(min(1.0, max(0.0, recall_score)), 4), reasons

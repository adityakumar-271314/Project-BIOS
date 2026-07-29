from typing import Tuple, List, Optional
from ..schemas import EpisodicEvent
from ..refinement.similarity import SignatureSimilarityEvaluator


class RedundancyEvaluator:
    """
    Evaluates whether an episode repeats neighboring or historical episode signatures.
    """

    def __init__(
        self,
        similarity_evaluator: Optional[SignatureSimilarityEvaluator] = None,
        redundancy_threshold: float = 0.75,
    ):
        self.evaluator = similarity_evaluator or SignatureSimilarityEvaluator()
        self.redundancy_threshold = redundancy_threshold

    def evaluate(
        self,
        event: EpisodicEvent,
        neighbors: Optional[List[EpisodicEvent]] = None,
    ) -> Tuple[float, List[str]]:
        reasons = []
        if not neighbors:
            return 0.0, []

        max_sim = 0.0
        for neighbor in neighbors:
            if (
                neighbor.start_tick == event.start_tick
                and neighbor.end_tick == event.end_tick
            ):
                continue  # Skip self

            sim = self.evaluator.compute_similarity(event.signature, neighbor.signature)

            # Boost similarity if time spans overlap heavily
            overlap_ratio = self._calculate_tick_overlap(event, neighbor)
            combined_redundancy = 0.7 * sim + 0.3 * overlap_ratio

            if combined_redundancy > max_sim:
                max_sim = combined_redundancy

        if max_sim >= self.redundancy_threshold:
            reasons.append(f"high_behavioral_overlap_{round(max_sim, 2)}")

        return round(max_sim, 4), reasons

    def _calculate_tick_overlap(self, ev1: EpisodicEvent, ev2: EpisodicEvent) -> float:
        overlap_start = max(ev1.start_tick, ev2.start_tick)
        overlap_end = min(ev1.end_tick, ev2.end_tick)
        overlap_ticks = max(0, overlap_end - overlap_start + 1)

        min_duration = min(
            ev1.end_tick - ev1.start_tick + 1, ev2.end_tick - ev2.start_tick + 1
        )
        return overlap_ticks / max(1, min_duration)

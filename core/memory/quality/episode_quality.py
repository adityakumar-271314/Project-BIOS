from typing import List, Optional, Tuple
from ..schemas import EpisodicEvent
from ..schemas import EpisodeQuality
from .coherence import CoherenceEvaluator
from .coverage import CoverageEvaluator
from .redundancy import RedundancyEvaluator
from .novelty import NoveltyEvaluator
from .recall import RecallUsefulnessEvaluator


class EpisodeQualityEvaluator:
    """
    Main orchestrator for Part G: Episode Quality Evaluation.

    Evaluates a batch or sequence of EpisodicEvents purely functionally,
    annotating each event with an immutable EpisodeQuality instance containing
    coherence, coverage, redundancy, novelty, recall usefulness, and diagnostic reasons.
    """

    def __init__(
        self,
        coherence_weight: float = 0.30,
        coverage_weight: float = 0.20,
        redundancy_weight: float = 0.15,
        novelty_weight: float = 0.15,
        recall_weight: float = 0.20,
        coherence_evaluator: Optional[CoherenceEvaluator] = None,
        coverage_evaluator: Optional[CoverageEvaluator] = None,
        redundancy_evaluator: Optional[RedundancyEvaluator] = None,
        novelty_evaluator: Optional[NoveltyEvaluator] = None,
        recall_evaluator: Optional[RecallUsefulnessEvaluator] = None,
    ):
        self.coherence_weight = coherence_weight
        self.coverage_weight = coverage_weight
        self.redundancy_weight = redundancy_weight
        self.novelty_weight = novelty_weight
        self.recall_weight = recall_weight

        # Initialize sub-evaluators
        self.coherence_evaluator = coherence_evaluator or CoherenceEvaluator()
        self.coverage_evaluator = coverage_evaluator or CoverageEvaluator()
        self.redundancy_evaluator = redundancy_evaluator or RedundancyEvaluator()
        self.novelty_evaluator = novelty_evaluator or NoveltyEvaluator()
        self.recall_evaluator = recall_evaluator or RecallUsefulnessEvaluator()

    def evaluate_episode(
        self,
        event: EpisodicEvent,
        neighbors: Optional[List[EpisodicEvent]] = None,
        history: Optional[List[EpisodicEvent]] = None,
    ) -> Tuple[EpisodeQuality, List[str]]:
        """
        Evaluates a single EpisodicEvent, returning its EpisodeQuality and ephemeral diagnostic reasons.
        """
        all_reasons: List[str] = []

        coherence, coherence_reasons = self.coherence_evaluator.evaluate(event)
        all_reasons.extend(coherence_reasons)

        coverage, coverage_reasons = self.coverage_evaluator.evaluate(event)
        all_reasons.extend(coverage_reasons)

        redundancy, redundancy_reasons = self.redundancy_evaluator.evaluate(
            event, neighbors=neighbors
        )
        all_reasons.extend(redundancy_reasons)

        novelty, novelty_reasons = self.novelty_evaluator.evaluate(
            event, history=history
        )
        all_reasons.extend(novelty_reasons)

        recall_usefulness, recall_reasons = self.recall_evaluator.evaluate(
            event, coherence_score=coherence
        )
        all_reasons.extend(recall_reasons)

        overall_quality = (
            (self.coherence_weight * coherence)
            + (self.coverage_weight * coverage)
            + (self.redundancy_weight * (1.0 - redundancy))
            + (self.novelty_weight * novelty)
            + (self.recall_weight * recall_usefulness)
        )
        overall_quality = round(min(1.0, max(0.0, overall_quality)), 4)

        quality = EpisodeQuality(
            coherence=coherence,
            coverage=coverage,
            redundancy=redundancy,
            novelty=novelty,
            recall_usefulness=recall_usefulness,
            overall_quality=overall_quality,
        )
        return quality, all_reasons

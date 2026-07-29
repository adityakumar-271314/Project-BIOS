from typing import List, Optional
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
    ) -> EpisodeQuality:
        """
        Evaluates a single EpisodicEvent and returns its EpisodeQuality score.
        """
        all_reasons: List[str] = []

        # 1. Coherence
        coherence, coherence_reasons = self.coherence_evaluator.evaluate(event)
        all_reasons.extend(coherence_reasons)

        # 2. Coverage
        coverage, coverage_reasons = self.coverage_evaluator.evaluate(event)
        all_reasons.extend(coverage_reasons)

        # 3. Redundancy (against neighbors)
        redundancy, redundancy_reasons = self.redundancy_evaluator.evaluate(
            event, neighbors=neighbors
        )
        all_reasons.extend(redundancy_reasons)

        # 4. Novelty (against history/batch)
        novelty, novelty_reasons = self.novelty_evaluator.evaluate(
            event, history=history
        )
        all_reasons.extend(novelty_reasons)

        # 5. Recall Usefulness (gated by coherence)
        recall_usefulness, recall_reasons = self.recall_evaluator.evaluate(
            event, coherence_score=coherence
        )
        all_reasons.extend(recall_reasons)

        # 6. Overall Composite Quality Score
        # High redundancy penalizes overall quality: (1.0 - redundancy)
        overall_quality = (
            (self.coherence_weight * coherence)
            + (self.coverage_weight * coverage)
            + (self.redundancy_weight * (1.0 - redundancy))
            + (self.novelty_weight * novelty)
            + (self.recall_weight * recall_usefulness)
        )
        overall_quality = round(min(1.0, max(0.0, overall_quality)), 4)

        return EpisodeQuality(
            coherence=coherence,
            coverage=coverage,
            redundancy=redundancy,
            novelty=novelty,
            recall_usefulness=recall_usefulness,
            overall_quality=overall_quality,
            reasons=tuple(sorted(set(all_reasons))),
        )

    def evaluate_batch(
        self,
        events: List[EpisodicEvent],
        history: Optional[List[EpisodicEvent]] = None,
    ) -> List[EpisodicEvent]:
        """
        Evaluates and attaches EpisodeQuality to a sequence of EpisodicEvents.
        Performs in-place quality annotation of events in the batch.
        """
        if not events:
            return []

        for event in events:
            # Use current batch as neighbors for redundancy check
            quality = self.evaluate_episode(
                event=event,
                neighbors=events,
                history=history,
            )
            event.quality = quality

        return events

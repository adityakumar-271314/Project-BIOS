import math
from typing import Tuple, List
from ..schemas import EpisodicEvent


class CoverageEvaluator:
    """
    Evaluates whether enough of the behavioral event was captured cleanly,
    checking boundary integrity and outcome/summary completeness.
    """

    def evaluate(self, event: EpisodicEvent) -> Tuple[float, List[str]]:
        reasons = []
        sig = event.signature
        duration = max(1, sig.duration_ticks)

        # 1. Boundary Completeness Check
        boundary_score = 1.0
        notes = event.notes or ""
        if "truncated" in notes.lower() or duration <= 3:
            boundary_score *= 0.6
            reasons.append("short_or_truncated_duration")

        # 2. Signature Summary & Outcome Completeness
        summary_score = 1.0
        if not sig.net_resource_deltas or not sig.resource_summaries:
            summary_score = 0.7
            reasons.append("incomplete_resource_summaries")

        if sig.outcome_status.value == "unknown":
            summary_score *= 0.8
            reasons.append("unknown_outcome_status")

        coverage = (0.6 * boundary_score) + (0.4 * summary_score)
        return round(coverage, 4), reasons

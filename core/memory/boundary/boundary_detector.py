from typing import List, Dict, Any, Optional
from ..schemas import EpisodeFrame
from .boundary import BoundaryInterval
from .boundary_rules import BoundaryRules
from .boundary_score import BoundaryScore
from .boundary_validator import BoundaryValidator


class BoundaryDetector:
    """
    Main orchestrator for Stage 1 — Part B: Boundary Detection.

    Processes chronological EpisodeFrame sequences through BoundaryRules -> BoundaryScore
    -> BoundaryValidator to detect, score, and emit validated BoundaryIntervals.
    """

    def __init__(
        self,
        min_duration: int = 15,
        min_separation: int = 30,
        min_start_confidence: float = 0.61,
        min_end_confidence: float = 0.54,
        rule_weight: float = 0.6,
        metric_weight: float = 0.4,
    ):
        self.rules_engine = BoundaryRules()
        self.scoring_engine = BoundaryScore(
            rule_weight=rule_weight,
            metric_weight=metric_weight,
        )
        self.validator = BoundaryValidator(
            min_duration=min_duration,
            min_separation=min_separation,
            min_start_confidence=min_start_confidence,
            min_end_confidence=min_end_confidence,
        )

    def detect_boundaries(self, frames: List[EpisodeFrame]) -> List[BoundaryInterval]:
        if not frames or len(frames) < 2:
            return []

        start_candidates: List[Dict[str, Any]] = []
        end_candidates: List[Dict[str, Any]] = []

        for i in range(1, len(frames)):
            curr_frame = frames[i]
            curr_tick = curr_frame.snapshot.tick

            window_start = max(0, i - 4)
            recent_window = frames[window_start : i + 1]
            prev_frame = frames[i - 1]

            start_triggers, end_triggers = self.rules_engine.evaluate(
                prev_frame=prev_frame,
                curr_frame=curr_frame,
            )

            start_conf, start_reasons, end_conf, end_reasons = (
                self.scoring_engine.score_frame(
                    recent_frames=recent_window,
                    start_triggers=start_triggers,
                    end_triggers=end_triggers,
                )
            )

            # STEP 1 TUNING: Lowered recording floor from 0.35 to 0.30
            if start_conf > 0.30:
                start_candidates.append(
                    {
                        "tick": curr_tick,
                        "confidence": start_conf,
                        "reasons": start_reasons,
                    }
                )

            if end_conf > 0.30:
                end_candidates.append(
                    {
                        "tick": curr_tick,
                        "confidence": end_conf,
                        "reasons": end_reasons,
                    }
                )

        max_tick = frames[-1].snapshot.tick

        return self.validator.filter_and_pair(
            start_candidates=start_candidates,
            end_candidates=end_candidates,
            max_tick=max_tick,
        )
from typing import List, Tuple, Dict, Any
from .boundary import BoundaryInterval


class BoundaryValidator:
    """
    Validates boundary candidates, filters noise/oscillations, and enforces temporal 
    hygiene to produce structured BoundaryInterval instances.
    """

    def __init__(
        self,
        min_duration: int = 15,
        min_separation: int = 30,
        min_start_confidence: float = 0.4,
        min_end_confidence: float = 0.35,
    ):
        """
        Args:
            min_duration: Minimum duration (in ticks) for a valid interval.
            min_separation: Minimum ticks required between consecutive interval starts.
            min_start_confidence: Confidence floor for accepting a start boundary.
            min_end_confidence: Confidence floor for accepting an end boundary.
        """
        self.min_duration = min_duration
        self.min_separation = min_separation
        self.min_start_confidence = min_start_confidence
        self.min_end_confidence = min_end_confidence

    def filter_and_pair(
        self,
        start_candidates: List[Dict[str, Any]],
        end_candidates: List[Dict[str, Any]],
        max_tick: int,
    ) -> List[BoundaryInterval]:
        """
        Pairs detected start and end boundary points into validated BoundaryIntervals.

        Args:
            start_candidates: List of dicts containing 'tick', 'confidence', 'reasons'.
            end_candidates: List of dicts containing 'tick', 'confidence', 'reasons'.
            max_tick: The maximum tick in the processed frame window (used for unclosed intervals).

        Returns:
            List of validated and cleaned BoundaryInterval instances.
        """
        # 1. Filter candidates by confidence thresholds
        valid_starts = [
            s for s in start_candidates if s["confidence"] >= self.min_start_confidence
        ]
        valid_ends = [
            e for e in end_candidates if e["confidence"] >= self.min_end_confidence
        ]

        if not valid_starts:
            return []

        # Sort chronologically
        valid_starts.sort(key=lambda x: x["tick"])
        valid_ends.sort(key=lambda x: x["tick"])

        raw_intervals: List[BoundaryInterval] = []

        # 2. Pair starts with matching end points
        for i, start in enumerate(valid_starts):
            s_tick = start["tick"]

            # Next start tick to cap this interval's search boundary
            next_start_tick = (
                valid_starts[i + 1]["tick"] if i + 1 < len(valid_starts) else max_tick + 1
            )

            # Find matching ends occurring after start_tick and before next_start_tick
            matching_ends = [
                e for e in valid_ends if s_tick < e["tick"] <= next_start_tick
            ]

            if matching_ends:
                # Select the strongest or last matching end event
                best_end = max(matching_ends, key=lambda x: x["confidence"])
                e_tick = best_end["tick"]
                e_conf = best_end["confidence"]
                e_reasons = best_end["reasons"]
            else:
                # Default end tick if no clean end boundary was triggered before next start/window end
                e_tick = min(next_start_tick - 1, max_tick)
                e_conf = 0.3
                e_reasons = ["window_fallback_end"]

            interval = BoundaryInterval(
                start_tick=s_tick,
                end_tick=e_tick,
                start_confidence=start["confidence"],
                end_confidence=e_conf,
                start_reasons=start["reasons"],
                end_reasons=e_reasons,
            )
            raw_intervals.append(interval)

        # 3. Apply temporal hygiene rules
        return self._apply_hygiene_rules(raw_intervals)

    def _apply_hygiene_rules(
        self, intervals: List[BoundaryInterval]
    ) -> List[BoundaryInterval]:
        """Filters out short duration intervals, oscillations, and close overlaps."""
        if not intervals:
            return []

        cleaned: List[BoundaryInterval] = []

        for interval in intervals:
            # Rule A: Enforce proper start_tick < end_tick ordering & minimum duration
            if interval.duration < self.min_duration:
                continue

            # Rule B: Enforce minimum separation between consecutive boundaries
            if cleaned:
                prev = cleaned[-1]
                if interval.start_tick - prev.start_tick < self.min_separation:
                    # Merge or keep the higher confidence interval
                    if interval.start_confidence > prev.start_confidence:
                        cleaned[-1] = interval
                    continue

            cleaned.append(interval)

        return cleaned
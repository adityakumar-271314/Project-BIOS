import math
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from ..schemas import EpisodicEvent, EpisodeSignature


@dataclass(slots=True, frozen=True)
class RelationshipScore:
    """Detailed breakdown of affinity scores between two episodic events."""

    event_a_id: str
    event_b_id: str
    overall_score: float
    behavioral_score: float
    temporal_score: float
    spatial_score: float
    causal_score: float
    primary_relationship_type: str  # e.g., "sequential_continuation", "shared_goal", "causal_transition", "unrelated"
    details: Dict[str, Any] = field(default_factory=dict)


class RelationshipAnalyzer:
    """
    Analyzes pairwise and sequential relationships between finalized EpisodicEvents.
    Uses strictly signature data, spatial endpoints, and tick boundaries without touching raw frames.
    """

    def __init__(
        self,
        max_temporal_gap_ticks: int = 600,
        max_spatial_distance: float = 100.0,
        weight_behavior: float = 0.35,
        weight_temporal: float = 0.25,
        weight_spatial: float = 0.20,
        weight_causal: float = 0.20,
        min_affinity_threshold: float = 0.40,
    ):
        self.max_temporal_gap_ticks = max_temporal_gap_ticks
        self.max_spatial_distance = max_spatial_distance
        self.weight_behavior = weight_behavior
        self.weight_temporal = weight_temporal
        self.weight_spatial = weight_spatial
        self.weight_causal = weight_causal
        self.min_affinity_threshold = min_affinity_threshold

    def analyze_pair(
        self,
        event_a: EpisodicEvent,
        event_b: EpisodicEvent,
        id_a: str,
        id_b: str,
    ) -> RelationshipScore:
        """Evaluates pairwise relationship between event A and event B."""
        sig_a = event_a.signature
        sig_b = event_b.signature

        # 1. Behavioral Continuity
        behavior_score, behavior_details = self._calc_behavioral_score(sig_a, sig_b)

        # 2. Temporal Proximity
        temporal_score, gap_ticks = self._calc_temporal_score(event_a, event_b)

        # 3. Spatial Continuity
        spatial_score, distance = self._calc_spatial_score(event_a, event_b)

        # 4. Causal Transition
        causal_score, causal_reason = self._calc_causal_score(
            sig_a, sig_b, event_a, event_b
        )

        # Weighted Composite Score
        overall_score = (
            self.weight_behavior * behavior_score
            + self.weight_temporal * temporal_score
            + self.weight_spatial * spatial_score
            + self.weight_causal * causal_score
        )

        # Determine primary relationship label
        rel_type = self._determine_relationship_type(
            overall_score=overall_score,
            behavior_score=behavior_score,
            causal_score=causal_score,
            temporal_score=temporal_score,
            spatial_score=spatial_score,
            causal_reason=causal_reason,
        )

        details = {
            "gap_ticks": gap_ticks,
            "spatial_distance": distance,
            "causal_reason": causal_reason,
            **behavior_details,
        }

        return RelationshipScore(
            event_a_id=id_a,
            event_b_id=id_b,
            overall_score=round(overall_score, 4),
            behavioral_score=round(behavior_score, 4),
            temporal_score=round(temporal_score, 4),
            spatial_score=round(spatial_score, 4),
            causal_score=round(causal_score, 4),
            primary_relationship_type=rel_type,
            details=details,
        )

    def analyze_sequence(
        self,
        events: List[Tuple[str, EpisodicEvent]],
    ) -> List[RelationshipScore]:
        """Analyzes adjacent pairs in a chronologically sorted sequence of events."""
        scores = []
        for i in range(len(events) - 1):
            id_a, ev_a = events[i]
            id_b, ev_b = events[i + 1]
            scores.append(self.analyze_pair(ev_a, ev_b, id_a, id_b))
        return scores

    # --- PRIVATE HELPERS ---

    def _calc_behavioral_score(
        self, sig_a: EpisodeSignature, sig_b: EpisodeSignature
    ) -> Tuple[float, Dict[str, Any]]:
        matches = 0
        total_factors = 0

        # Goal Match
        goal_match = False
        if sig_a.dominant_goal and sig_b.dominant_goal:
            total_factors += 1
            if sig_a.dominant_goal == sig_b.dominant_goal:
                matches += 1
                goal_match = True

        # Skill Match
        skill_match = False
        if sig_a.dominant_skill and sig_b.dominant_skill:
            total_factors += 1
            if sig_a.dominant_skill == sig_b.dominant_skill:
                matches += 1
                skill_match = True

        # Target Match
        target_match = False
        if sig_a.dominant_target and sig_b.dominant_target:
            total_factors += 1
            if sig_a.dominant_target == sig_b.dominant_target:
                matches += 1
                target_match = True

        if total_factors == 0:
            score = 0.5  # Neutral fallback when no categorical behavioral traits exist
        else:
            score = matches / total_factors

        details = {
            "goal_match": goal_match,
            "skill_match": skill_match,
            "target_match": target_match,
        }
        return score, details

    def _calc_temporal_score(
        self, ev_a: EpisodicEvent, ev_b: EpisodicEvent
    ) -> Tuple[float, int]:
        # Ensure chronological ordering (a -> b)
        if ev_b.start_tick >= ev_a.end_tick:
            gap = ev_b.start_tick - ev_a.end_tick
        else:
            gap = abs(ev_a.start_tick - ev_b.start_tick)

        if gap == 0:
            return 1.0, 0

        if gap > self.max_temporal_gap_ticks:
            return 0.0, gap

        # Exponential decay over gap ticks
        decay_factor = 3.0 / self.max_temporal_gap_ticks
        score = math.exp(-decay_factor * gap)
        return score, gap

    def _calc_spatial_score(
        self, ev_a: EpisodicEvent, ev_b: EpisodicEvent
    ) -> Tuple[float, float]:
        # Distance from end position of A to start position of B
        dx = ev_b.start_x - ev_a.end_x
        dy = ev_b.start_y - ev_a.end_y
        dist = math.hypot(dx, dy)

        if dist >= self.max_spatial_distance:
            return 0.0, dist

        score = 1.0 - (dist / self.max_spatial_distance)
        return max(0.0, score), dist

    def _calc_causal_score(
        self,
        sig_a: EpisodeSignature,
        sig_b: EpisodeSignature,
        ev_a: EpisodicEvent,
        ev_b: EpisodicEvent,
    ) -> Tuple[float, str]:
        # 1. Goal completion leading to a new goal
        if sig_a.outcome_completed and sig_a.dominant_goal != sig_b.dominant_goal:
            return 0.9, "goal_completion_handoff"

        # 2. Sequential goal transition matching
        if sig_a.goal_transitions and sig_b.dominant_goal:
            last_trans = sig_a.goal_transitions[-1]
            if last_trans.to_state == sig_b.dominant_goal:
                return 1.0, "direct_goal_transition"

        # 3. High threat/hazard driving behavioral reaction
        if sig_a.max_hazard_exposure > 0.5 and sig_b.dominant_skill in (
            "flee",
            "evade",
            "defense",
        ):
            return 0.85, "hazard_reaction"

        return 0.0, "none"

    def _determine_relationship_type(
        self,
        overall_score: float,
        behavior_score: float,
        causal_score: float,
        temporal_score: float,
        spatial_score: float,
        causal_reason: str,
    ) -> str:
        if overall_score < self.min_affinity_threshold:
            return "unrelated"

        if causal_score >= 0.8:
            return f"causal_{causal_reason}"

        if behavior_score >= 0.8 and temporal_score >= 0.5:
            return "same_task_continuation"

        if spatial_score >= 0.7 and temporal_score >= 0.7:
            return "spatial_temporal_proximity"

        if behavior_score >= 0.5:
            return "shared_context"

        return "weak_sequence"

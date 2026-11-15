from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
from ..schemas import EpisodicEvent, EpisodeHierarchy, EpisodeSignature, HierarchyLevel, OutcomeStatus, StateSummary

class SummaryAggregator:
    """
    Synthesizes higher-tier hierarchy nodes (Group, Mission, Narrative) 
    strictly from child signatures and quality metrics without duplicating raw telemetry[cite: 1].
    """

    @staticmethod
    def aggregate_signatures(signatures: List[EpisodeSignature]) -> EpisodeSignature:
        if not signatures:
            return EpisodeSignature()

        goals = [s.dominant_goal for s in signatures if s.dominant_goal]
        skills = [s.dominant_skill for s in signatures if s.dominant_skill]
        targets = [s.dominant_target for s in signatures if s.dominant_target]

        dom_goal = Counter(goals).most_common(1)[0][0] if goals else None
        dom_skill = Counter(skills).most_common(1)[0][0] if skills else None
        dom_target = Counter(targets).most_common(1)[0][0] if targets else None

        # Net resource deltas aggregation
        net_deltas: Dict[str, float] = {}
        for sig in signatures:
            for k, v in sig.net_resource_deltas.items():
                net_deltas[k] = net_deltas.get(k, 0.0) + v

        # Peak emotions aggregation
        max_emotions: Dict[str, float] = {}
        for sig in signatures:
            for k, v in sig.peak_emotions.items():
                max_emotions[k] = max(max_emotions.get(k, 0.0), v)

        max_hazard = max((s.max_hazard_exposure for s in signatures), default=0.0)
        max_reward = max((s.max_reward_exposure for s in signatures), default=0.0)
        
        landmark_counts = [s.nearest_landmark_id for s in signatures if s.nearest_landmark_id is not None]
        nearest_landmark_id = Counter(landmark_counts).most_common(1)[0][0] if landmark_counts else None

        outcomes = [s.outcome_status for s in signatures if s.outcome_status != OutcomeStatus.UNKNOWN]
        outcome_status = outcomes[-1] if outcomes else OutcomeStatus.COMPLETED

        total_duration = sum(s.duration_ticks for s in signatures)

        return EpisodeSignature(
            dominant_goal=dom_goal,
            dominant_skill=dom_skill,
            dominant_target=dom_target,
            semantic_event_type="aggregated_cluster",
            outcome_status=outcome_status,
            net_resource_deltas=net_deltas,
            peak_emotions=max_emotions,
            max_hazard_exposure=max_hazard,
            max_reward_exposure=max_reward,
            nearest_landmark_id=nearest_landmark_id,
            duration_ticks=total_duration,
        )

    @classmethod
    def create_hierarchy_unit(
        cls,
        hierarchy_id: str,
        level: HierarchyLevel,
        root_id: str,
        events: List[EpisodicEvent],
        qualities: List[float],
        importances: List[float],
        parent_id: Optional[str] = None
    ) -> EpisodeHierarchy:
        if not events:
            return EpisodeHierarchy(hierarchy_id=hierarchy_id, level=level, root_id=root_id)

        start_tick = events[0].start_tick
        end_tick = events[-1].end_tick
        duration_ticks = end_tick - start_tick + 1

        signatures = [e.signature for e in events]
        dominant_signature = cls.aggregate_signatures(signatures)

        overall_quality = sum(qualities) / len(qualities) if qualities else 1.0
        overall_importance = sum(importances) / len(importances) if importances else 0.0

        episode_ids = tuple(str(e.peak_tick) for e in events) # or unique identifier mapping

        return EpisodeHierarchy(
            hierarchy_id=hierarchy_id,
            level=level,
            root_id=root_id,
            episode_ids=episode_ids,
            parent_hierarchy_id=parent_id,
            start_tick=start_tick,
            end_tick=end_tick,
            duration_ticks=duration_ticks,
            dominant_signature=dominant_signature,
            overall_quality=overall_quality,
            overall_importance=overall_importance,
        )
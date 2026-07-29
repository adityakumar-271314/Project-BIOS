import uuid
from typing import List, Dict, Any, Tuple, Optional
from ..schemas import (
    EpisodicEvent,
    EpisodeSignature,
    EpisodeNode,
    EpisodeHierarchy,
    HierarchyLevel,
    StateSummary,
)
from .relationship_analyzer import RelationshipAnalyzer, RelationshipScore


class HierarchyBuilder:
    """
    Constructs multi-level episodic hierarchies (Episodes -> Groups -> Missions -> Narratives)
    from finalized EpisodicEvents using signature metadata and relationship scores.
    """

    def __init__(
        self,
        relationship_analyzer: Optional[RelationshipAnalyzer] = None,
        group_affinity_threshold: float = 0.45,
        mission_affinity_threshold: float = 0.35,
    ):
        self.analyzer = relationship_analyzer or RelationshipAnalyzer()
        self.group_affinity_threshold = group_affinity_threshold
        self.mission_affinity_threshold = mission_affinity_threshold

    def build_hierarchy(
        self,
        events: List[EpisodicEvent],
        hierarchy_id_prefix: str = "hier",
    ) -> Tuple[List[EpisodeNode], List[EpisodeHierarchy]]:
        """
        Main entry point for Part D hierarchy construction.
        Given a list of finalized EpisodicEvents, produces:
          1. A list of EpisodeNodes representing graph positions and parent/child/sibling links.
          2. A list of EpisodeHierarchy containers (Groups, Missions, Narratives).
        """
        if not events:
            return [], []

        # Sort events chronologically by start_tick
        sorted_events = sorted(events, key=lambda e: e.start_tick)
        event_pairs: List[Tuple[str, EpisodicEvent]] = [
            (f"ep_{e.start_tick}_{e.end_tick}", e) for e in sorted_events
        ]

        # 1. Analyze sequential relationships
        rel_scores = self.analyzer.analyze_sequence(event_pairs)
        score_lookup: Dict[Tuple[str, str], RelationshipScore] = {
            (s.event_a_id, s.event_b_id): s for s in rel_scores
        }

        # 2. Build leaf EpisodeNodes for individual episodes
        leaf_nodes: Dict[str, EpisodeNode] = {}
        for i, (ep_id, event) in enumerate(event_pairs):
            prev_id = event_pairs[i - 1][0] if i > 0 else None
            next_id = event_pairs[i + 1][0] if i < len(event_pairs) - 1 else None

            rel_types = {}
            if prev_id and (prev_id, ep_id) in score_lookup:
                rel_types[prev_id] = score_lookup[
                    (prev_id, ep_id)
                ].primary_relationship_type
            if next_id and (ep_id, next_id) in score_lookup:
                rel_types[next_id] = score_lookup[
                    (ep_id, next_id)
                ].primary_relationship_type

            leaf_nodes[ep_id] = EpisodeNode(
                node_id=ep_id,
                level=HierarchyLevel.EPISODE,
                episode_id=ep_id,
                prev_id=prev_id,
                next_id=next_id,
                relationship_types=rel_types,
            )

        # 3. Group episodes into LEVEL 1 (GROUPS)
        groups, updated_leaf_nodes = self._cluster_into_level(
            items=event_pairs,
            level=HierarchyLevel.GROUP,
            id_prefix=f"{hierarchy_id_prefix}_grp",
            affinity_threshold=self.group_affinity_threshold,
            score_lookup=score_lookup,
            existing_nodes=leaf_nodes,
        )

        all_hierarchical_units: List[EpisodeHierarchy] = list(groups)

        # 4. Cluster Groups into LEVEL 2 (MISSIONS) if multiple groups exist
        if len(groups) > 1:
            group_items = [(g.hierarchy_id, g) for g in groups]
            missions, _ = self._cluster_hierarchical_units(
                units=groups,
                level=HierarchyLevel.MISSION,
                id_prefix=f"{hierarchy_id_prefix}_msn",
                affinity_threshold=self.mission_affinity_threshold,
            )
            all_hierarchical_units.extend(missions)

            # 5. Cluster Missions into LEVEL 3 (NARRATIVES) if multiple missions exist
            if len(missions) > 1:
                narratives, _ = self._cluster_hierarchical_units(
                    units=missions,
                    level=HierarchyLevel.NARRATIVE,
                    id_prefix=f"{hierarchy_id_prefix}_nar",
                    affinity_threshold=self.mission_affinity_threshold * 0.8,
                )
                all_hierarchical_units.extend(narratives)

        return list(updated_leaf_nodes.values()), all_hierarchical_units

    # --- PRIVATE CLUSTERING HELPERS ---

    def _cluster_into_level(
        self,
        items: List[Tuple[str, EpisodicEvent]],
        level: HierarchyLevel,
        id_prefix: str,
        affinity_threshold: float,
        score_lookup: Dict[Tuple[str, str], RelationshipScore],
        existing_nodes: Dict[str, EpisodeNode],
    ) -> Tuple[List[EpisodeHierarchy], Dict[str, EpisodeNode]]:
        hierarchies: List[EpisodeHierarchy] = []
        nodes_copy = dict(existing_nodes)

        current_cluster: List[Tuple[str, EpisodicEvent]] = [items[0]]

        for i in range(len(items) - 1):
            curr_id, curr_ev = items[i]
            next_id, next_ev = items[i + 1]

            score_obj = score_lookup.get((curr_id, next_id))
            score_val = score_obj.overall_score if score_obj else 0.0

            if score_val >= affinity_threshold:
                current_cluster.append((next_id, next_ev))
            else:
                # Flush current cluster into a hierarchy unit
                grp = self._create_hierarchy_unit(
                    current_cluster, level, f"{id_prefix}_{len(hierarchies)}"
                )
                hierarchies.append(grp)
                current_cluster = [(next_id, next_ev)]

        if current_cluster:
            grp = self._create_hierarchy_unit(
                current_cluster, level, f"{id_prefix}_{len(hierarchies)}"
            )
            hierarchies.append(grp)

        # Update parent references in leaf nodes
        for grp in hierarchies:
            for ep_id in grp.episode_ids:
                old_node = nodes_copy[ep_id]
                nodes_copy[ep_id] = EpisodeNode(
                    node_id=old_node.node_id,
                    level=old_node.level,
                    episode_id=old_node.episode_id,
                    parent_id=grp.hierarchy_id,
                    child_ids=old_node.child_ids,
                    prev_id=old_node.prev_id,
                    next_id=old_node.next_id,
                    relationship_types=old_node.relationship_types,
                )

        return hierarchies, nodes_copy

    def _cluster_hierarchical_units(
        self,
        units: List[EpisodeHierarchy],
        level: HierarchyLevel,
        id_prefix: str,
        affinity_threshold: float,
    ) -> Tuple[List[EpisodeHierarchy], List[EpisodeHierarchy]]:
        """Aggregates child hierarchy units into higher-level parent units."""
        parents: List[EpisodeHierarchy] = []
        updated_children: List[EpisodeHierarchy] = []

        current_cluster: List[EpisodeHierarchy] = [units[0]]

        for i in range(len(units) - 1):
            curr_u = units[i]
            next_u = units[i + 1]

            # Measure overlap / continuity between units
            shared_goal = (
                curr_u.dominant_signature.dominant_goal
                and curr_u.dominant_signature.dominant_goal
                == next_u.dominant_signature.dominant_goal
            )
            tick_gap = max(0, next_u.start_tick - curr_u.end_tick)

            # Continuity condition
            if shared_goal or tick_gap < self.analyzer.max_temporal_gap_ticks:
                current_cluster.append(next_u)
            else:
                parent = self._merge_units_into_parent(
                    current_cluster, level, f"{id_prefix}_{len(parents)}"
                )
                parents.append(parent)
                current_cluster = [next_u]

        if current_cluster:
            parent = self._merge_units_into_parent(
                current_cluster, level, f"{id_prefix}_{len(parents)}"
            )
            parents.append(parent)

        # Update parent links on children
        parent_map = {
            c_id: p.hierarchy_id for p in parents for c_id in p.child_hierarchy_ids
        }
        for u in units:
            p_id = parent_map.get(u.hierarchy_id)
            updated_children.append(
                EpisodeHierarchy(
                    hierarchy_id=u.hierarchy_id,
                    level=u.level,
                    root_id=u.root_id,
                    episode_ids=u.episode_ids,
                    child_hierarchy_ids=u.child_hierarchy_ids,
                    parent_hierarchy_id=p_id,
                    start_tick=u.start_tick,
                    end_tick=u.end_tick,
                    duration_ticks=u.duration_ticks,
                    dominant_signature=u.dominant_signature,
                    overall_quality=u.overall_quality,
                    overall_importance=u.overall_importance,
                    metadata=u.metadata,
                )
            )

        return parents, updated_children

    def _create_hierarchy_unit(
        self,
        cluster: List[Tuple[str, EpisodicEvent]],
        level: HierarchyLevel,
        unit_id: str,
    ) -> EpisodeHierarchy:
        ep_ids = tuple(item[0] for item in cluster)
        events = [item[1] for item in cluster]

        start_tick = events[0].start_tick
        end_tick = events[-1].end_tick
        duration = end_tick - start_tick

        agg_signature = self._aggregate_signatures(
            [e.signature for e in events], duration
        )
        avg_quality = sum(
            (e.quality.overall_quality if e.quality else 1.0) for e in events
        ) / len(events)
        avg_importance = sum(e.signature.overall_importance for e in events) / len(
            events
        )

        return EpisodeHierarchy(
            hierarchy_id=unit_id,
            level=level,
            root_id=ep_ids[0],
            episode_ids=ep_ids,
            child_hierarchy_ids=(),
            parent_hierarchy_id=None,
            start_tick=start_tick,
            end_tick=end_tick,
            duration_ticks=duration,
            dominant_signature=agg_signature,
            overall_quality=round(avg_quality, 4),
            overall_importance=round(avg_importance, 4),
            metadata={"member_count": len(events)},
        )

    def _merge_units_into_parent(
        self,
        cluster: List[EpisodeHierarchy],
        level: HierarchyLevel,
        unit_id: str,
    ) -> EpisodeHierarchy:
        child_hierarchy_ids = tuple(u.hierarchy_id for u in cluster)
        all_ep_ids = tuple(ep for u in cluster for ep in u.episode_ids)

        start_tick = cluster[0].start_tick
        end_tick = cluster[-1].end_tick
        duration = end_tick - start_tick

        agg_signature = self._aggregate_signatures(
            [u.dominant_signature for u in cluster], duration
        )
        avg_quality = sum(u.overall_quality for u in cluster) / len(cluster)
        avg_importance = sum(u.overall_importance for u in cluster) / len(cluster)

        return EpisodeHierarchy(
            hierarchy_id=unit_id,
            level=level,
            root_id=cluster[0].root_id,
            episode_ids=all_ep_ids,
            child_hierarchy_ids=child_hierarchy_ids,
            parent_hierarchy_id=None,
            start_tick=start_tick,
            end_tick=end_tick,
            duration_ticks=duration,
            dominant_signature=agg_signature,
            overall_quality=round(avg_quality, 4),
            overall_importance=round(avg_importance, 4),
            metadata={"child_units": len(cluster)},
        )

    def _aggregate_signatures(
        self,
        signatures: List[EpisodeSignature],
        total_duration: int,
    ) -> EpisodeSignature:
        if not signatures:
            return EpisodeSignature()

        # Majority vote for dominant goal, skill, target
        goals = [s.dominant_goal for s in signatures if s.dominant_goal]
        skills = [s.dominant_skill for s in signatures if s.dominant_skill]
        targets = [s.dominant_target for s in signatures if s.dominant_target]

        dom_goal = max(set(goals), key=goals.count) if goals else None
        dom_skill = max(set(skills), key=skills.count) if skills else None
        dom_target = max(set(targets), key=targets.count) if targets else None

        avg_novelty = sum(s.overall_novelty for s in signatures) / len(signatures)
        avg_importance = sum(s.overall_importance for s in signatures) / len(signatures)
        max_hazard = max((s.max_hazard_exposure for s in signatures), default=0.0)
        max_reward = max((s.max_reward_exposure for s in signatures), default=0.0)

        return EpisodeSignature(
            dominant_goal=dom_goal,
            dominant_skill=dom_skill,
            dominant_target=dom_target,
            outcome_completed=any(s.outcome_completed for s in signatures),
            max_hazard_exposure=max_hazard,
            max_reward_exposure=max_reward,
            duration_ticks=total_duration,
            overall_novelty=round(avg_novelty, 4),
            overall_importance=round(avg_importance, 4),
        )

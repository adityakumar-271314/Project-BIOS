from __future__ import annotations
from typing import List, Dict, Any, Optional
from ..schemas import EpisodicEvent, EpisodeNode, EpisodeHierarchy, HierarchyLevel, HierarchyGraphState
from .config import HierarchyConfig
from .verifier import RelationshipVerifier
from .aggregator import SummaryAggregator

class HierarchyManager:
    """
    Manages incremental bottom-up clustering (Episode -> Group -> Mission -> Narrative)
    and graph state maintenance for persistence in hierarchy_index.json[cite: 1].
    """
    def __init__(self, config: Optional[HierarchyConfig] = None):
        self.config = config or HierarchyConfig()
        self.verifier = RelationshipVerifier(self.config)
        self.graph_state = HierarchyGraphState()
        self._episode_counter = 0

    def add_episode(self, event: EpisodicEvent, quality_score: float = 1.0, importance_score: float = 0.0) -> str:
        self._episode_counter += 1
        episode_id_str = f"episode_{self._episode_counter:06d}"
        node_id = f"node_ep_{self._episode_counter:06d}"

        # 1. Verify links with previous node if present
        prev_node_id = list(self.graph_state.nodes.keys())[-1] if self.graph_state.nodes else None
        prev_node = self.graph_state.nodes.get(prev_node_id) if prev_node_id else None

        relationship_types: Dict[str, str] = {}
        prev_id: Optional[str] = prev_node_id
        next_id: Optional[str] = None

        if prev_node and prev_node.episode_id:
            # Retrieve previous event summary or maintain links
            prev_id = prev_node.node_id
            prev_node_updated = EpisodeNode(
                node_id=prev_node.node_id,
                level=prev_node.level,
                episode_id=prev_node.episode_id,
                parent_id=prev_node.parent_id,
                child_ids=prev_node.child_ids,
                prev_id=prev_node.prev_id,
                next_id=node_id,
                relationship_types=prev_node.relationship_types
            )
            self.graph_state.nodes[prev_node.node_id] = prev_node_updated

        # Create Episode Node
        ep_node = EpisodeNode(
            node_id=node_id,
            level=HierarchyLevel.EPISODE,
            episode_id=episode_id_str,
            prev_id=prev_id,
            next_id=next_id,
            relationship_types=relationship_types
        )
        self.graph_state.nodes[node_id] = ep_node

        # 2. Assign to Group, Mission, Narrative hierarchy tiers
        self._cluster_into_hierarchies(event, node_id, quality_score, importance_score)
        return node_id

    def _cluster_into_hierarchies(self, event: EpisodicEvent, node_id: str, quality: float, importance: float) -> None:
        group_id = f"group_{len(self.graph_state.hierarchies) + 1:04d}"
        
        hierarchy_unit = SummaryAggregator.create_hierarchy_unit(
            hierarchy_id=group_id,
            level=HierarchyLevel.GROUP,
            root_id=group_id,
            events=[event],
            qualities=[quality],
            importances=[importance]
        )
        self.graph_state.hierarchies[group_id] = hierarchy_unit
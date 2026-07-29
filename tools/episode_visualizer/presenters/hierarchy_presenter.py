# FILE: tools/episode_visualizer/presenters/hierarchy_presenter.py
from typing import Dict, List, Optional

from core.memory.schemas import EpisodeHierarchy, EpisodeNode
from tools.episode_visualizer.presenters.schemas import (
    HierarchyNodeView,
    HierarchyView,
)


class HierarchyPresenter:
    """
    Pure presenter component that maps EpisodeHierarchy structures and EpisodeNode graph data
    into a unified HierarchyView layout.
    """

    @staticmethod
    def present(
        hierarchy: EpisodeHierarchy,
        nodes_map: Optional[Dict[str, EpisodeNode]] = None,
    ) -> HierarchyView:
        view_nodes: Dict[str, HierarchyNodeView] = {}

        # 1. Process explicit EpisodeNode graph if provided
        if nodes_map:
            for node_id, node in nodes_map.items():
                view_nodes[node_id] = HierarchyNodeView(
                    node_id=node.node_id,
                    level=(
                        node.level.value
                        if hasattr(node.level, "value")
                        else str(node.level)
                    ),
                    episode_id=node.episode_id,
                    parent_id=node.parent_id,
                    child_ids=tuple(node.child_ids),
                    prev_id=node.prev_id,
                    next_id=node.next_id,
                    relationship_types=dict(node.relationship_types),
                )
            root_id = (
                hierarchy.root_id
                if hierarchy.root_id in view_nodes
                else hierarchy.hierarchy_id
            )
            return HierarchyView(root_id=root_id, nodes=view_nodes)

        # 2. Fallback: Synthesize hierarchy node view from EpisodeHierarchy object
        level_str = (
            hierarchy.level.value
            if hasattr(hierarchy.level, "value")
            else str(hierarchy.level)
        )
        root_node = HierarchyNodeView(
            node_id=hierarchy.hierarchy_id,
            level=level_str,
            episode_id=hierarchy.root_id,
            parent_id=hierarchy.parent_hierarchy_id,
            child_ids=tuple(hierarchy.child_hierarchy_ids or hierarchy.episode_ids),
            start_tick=hierarchy.start_tick,
            end_tick=hierarchy.end_tick,
            overall_quality=hierarchy.overall_quality,
            overall_importance=hierarchy.overall_importance,
        )

        view_nodes[hierarchy.hierarchy_id] = root_node

        # Add leaf placeholders for child episode IDs
        for ep_id in hierarchy.episode_ids:
            if ep_id not in view_nodes:
                view_nodes[ep_id] = HierarchyNodeView(
                    node_id=ep_id,
                    level="episode",
                    episode_id=ep_id,
                    parent_id=hierarchy.hierarchy_id,
                )

        return HierarchyView(
            root_id=hierarchy.hierarchy_id,
            nodes=view_nodes,
        )

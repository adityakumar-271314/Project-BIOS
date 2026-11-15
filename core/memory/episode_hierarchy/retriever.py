from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
from ..schemas import HierarchyGraphState, EpisodeHierarchy, HierarchyLevel, EpisodeNode
from .config import HierarchyConfig

class HierarchyRetriever:
    """
    Implements top-down coarse-to-fine candidate selection, zero-load in-memory filtering,
    and neighborhood expansion over hierarchy and metadata indices.
    """
    def __init__(self, graph_state: HierarchyGraphState, metadata_index_data: dict, config: Optional[HierarchyConfig] = None):
        self.graph_state = graph_state
        self.metadata_index_data = metadata_index_data
        self.config = config or HierarchyConfig()

    def coarse_filter_hierarchies(
        self,
        target_goal: Optional[str] = None,
        target_skill: Optional[str] = None,
        outcome_status: Optional[str] = None,
        min_quality: float = 0.0,
        level: Optional[HierarchyLevel] = None
    ) -> List[EpisodeHierarchy]:
        """Evaluates high-level Mission, Group, or Narrative summaries in memory first."""
        matched = []
        for h_id, h_unit in self.graph_state.hierarchies.items():
            if level and h_unit.level != level:
                continue
            if h_unit.overall_quality < min_quality:
                continue
            if target_goal and h_unit.dominant_signature.dominant_goal != target_goal:
                continue
            if target_skill and h_unit.dominant_signature.dominant_skill != target_skill:
                continue
            if outcome_status and h_unit.dominant_signature.outcome_status != outcome_status:
                continue
            matched.append(h_unit)
        return matched

    def zero_load_retrieve_candidates(
        self,
        target_goal: Optional[str] = None,
        target_skill: Optional[str] = None,
        nearest_landmark_id: Optional[int] = None,
        min_quality: float = 0.25,
        top_k: int = 5
    ) -> List[int]:
        """
        Executes zero-load candidate filtering and ranking strictly in memory over indices
        before loading any full episode.json files from disk.
        """
        # 1. Coarse filter high-level hierarchy groups matching goal/skill
        matching_hierarchies = self.coarse_filter_hierarchies(
            target_goal=target_goal,
            target_skill=target_skill,
            min_quality=min_quality
        )

        valid_episode_numeric_ids = set()
        
        # Traverse child_ids downward to candidate episodes
        for h in matching_hierarchies:
            for ep_id_str in h.episode_ids:
                try:
                    # Extract numeric ID from string like "episode_000001" or parse string
                    numeric_id = int(ep_id_str.split("_")[-1]) if "_" in ep_id_str else int(ep_id_str)
                    valid_episode_numeric_ids.add(numeric_id)
                except ValueError:
                    continue

        # If no hierarchy matched directly, fallback to metadata index filtering
        episodes_meta = self.metadata_index_data.get("episodes", [])
        scored_candidates = []

        for meta in episodes_meta:
            eid = meta["id"]
            if valid_episode_numeric_ids and eid not in valid_episode_numeric_ids:
                # If hierarchical coarse filter was active, we can prioritize or restrict, 
                # but let's score all metadata entries for zero-load ranking
                pass

            # In-memory attribute checks
            if meta.get("overall_quality", 1.0) < min_quality:
                continue
            if target_goal and meta.get("dominant_goal") != target_goal:
                continue
            if target_skill and meta.get("dominant_skill") != target_skill:
                continue
            if nearest_landmark_id is not None and meta.get("nearest_landmark_id") != nearest_landmark_id:
                continue

            # Compute in-memory ranking score (combining quality and importance)
            quality = meta.get("overall_quality", 1.0)
            importance = meta.get("peak_significance", 0.0)
            score = (self.config.quality_weight * quality) + (self.config.importance_weight * importance)
            
            scored_candidates.append((score, eid))

        # Sort descending by score and return top-k numeric episode IDs
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        return [eid for _, eid in scored_candidates[:top_k]]

    def expand_neighborhood(self, node_id: str, hops: int = 1) -> List[str]:
        """Traverses prev_id, next_id, and causal edges to reconstruct surrounding events."""
        visited = set()
        queue = [(node_id, 0)]
        neighbor_nodes = []

        while queue:
            curr_id, current_hop = queue.pop(0)
            if curr_id in visited or current_hop > hops:
                continue
            visited.add(curr_id)
            if curr_id != node_id:
                neighbor_nodes.append(curr_id)

            node = self.graph_state.nodes.get(curr_id)
            if not node:
                continue

            # Add temporal neighbors
            if node.prev_id and node.prev_id not in visited:
                queue.append((node.prev_id, current_hop + 1))
            if node.next_id and node.next_id not in visited:
                queue.append((node.next_id, current_hop + 1))

            # Add relationship / causal neighbors
            for target_id in node.relationship_types.keys():
                if target_id not in visited:
                    queue.append((target_id, current_hop + 1))

        return neighbor_nodes
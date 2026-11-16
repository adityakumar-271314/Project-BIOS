from __future__ import annotations
from typing import List, Dict, Any, Optional
from collections import Counter


class HierarchyRetriever:
    """
    Implements top-down coarse-to-fine candidate selection, zero-load in-memory filtering,
    and lazy on-the-fly group synthesis directly from the unified memory index.
    """
    def __init__(self, unified_index_data: dict, config: Optional[Any] = None):
        self.index_data = unified_index_data
        self.config = config

    def coarse_filter_hierarchies(
        self,
        target_goal: Optional[str] = None,
        target_skill: Optional[str] = None,
        min_quality: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Evaluates high-level group summaries cached in the unified index.
        If no background groups have been flushed yet, synthesizes them lazily on-the-fly.
        """
        hierarchies = self.index_data.get("hierarchies", {})
        
        # Lazy fallback: If asynchronous consolidation hasn't run or hierarchies are empty,
        # dynamically cluster episodes in memory on-the-fly.
        if not hierarchies:
            hierarchies = self._synthesize_lazy_groups()

        matched = []
        for h_id, h_unit in hierarchies.items():
            if h_unit.get("overall_quality", 1.0) < min_quality:
                continue
            sig = h_unit.get("dominant_signature", {})
            if target_goal and sig.get("dominant_goal") != target_goal:
                continue
            if target_skill and sig.get("dominant_skill") != target_skill:
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
        Executes zero-load candidate filtering and ranking strictly in memory over the unified index
        before loading any full episode.json files from disk.
        """
        # 1. Coarse filter high-level group summaries matching goal/skill (with lazy synthesis fallback)
        matching_hierarchies = self.coarse_filter_hierarchies(
            target_goal=target_goal,
            target_skill=target_skill,
            min_quality=min_quality
        )

        valid_episode_numeric_ids = set()
        
        # Traverse child episode references downward
        for h in matching_hierarchies:
            for ep_id_str in h.get("episode_ids", []):
                try:
                    numeric_id = int(ep_id_str.split("_")[-1]) if "_" in ep_id_str else int(ep_id_str)
                    valid_episode_numeric_ids.add(numeric_id)
                except ValueError:
                    continue

        episodes_meta = self.index_data.get("episodes", [])
        scored_candidates = []

        for meta in episodes_meta:
            eid = meta["id"]

            # In-memory attribute checks
            if meta.get("overall_quality", 1.0) < min_quality:
                continue
            if target_goal and meta.get("dominant_goal") != target_goal:
                continue
            if target_skill and meta.get("dominant_skill") != target_skill:
                continue
            if nearest_landmark_id is not None and meta.get("nearest_landmark_id") != nearest_landmark_id:
                continue

            # Boost score if part of a high-level matched hierarchy cluster
            hierarchy_boost = 1.2 if (valid_episode_numeric_ids and eid in valid_episode_numeric_ids) else 1.0

            quality = meta.get("overall_quality", 1.0)
            importance = meta.get("peak_significance", 0.0)
            score = ((0.4 * quality) + (0.6 * importance)) * hierarchy_boost
            
            scored_candidates.append((score, eid))

        # Sort descending by score and return top-k numeric episode IDs
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        return [eid for _, eid in scored_candidates[:top_k]]

    def _synthesize_lazy_groups(self) -> Dict[str, Dict[str, Any]]:
        """
        Very basic lazy hierarchy synthesis: groups sequential episodes sharing 
        the same dominant goal or landmark on-the-fly during recall.
        """
        episodes = self.index_data.get("episodes", [])
        if not episodes:
            return {}

        lazy_hierarchies = {}
        current_cluster = []
        group_counter = 1

        for ep in episodes:
            if not current_cluster:
                current_cluster.append(ep)
                continue

            prev = current_cluster[-1]
            same_goal = (prev.get("dominant_goal") == ep.get("dominant_goal"))
            same_landmark = (prev.get("nearest_landmark_id") == ep.get("nearest_landmark_id"))

            if same_goal or same_landmark:
                current_cluster.append(ep)
            else:
                g_id = f"lazy_group_{group_counter:04d}"
                lazy_hierarchies[g_id] = self._build_lazy_summary(g_id, current_cluster)
                group_counter += 1
                current_cluster = [ep]

        if current_cluster:
            g_id = f"lazy_group_{group_counter:04d}"
            lazy_hierarchies[g_id] = self._build_lazy_summary(g_id, current_cluster)

        return lazy_hierarchies

    def _build_lazy_summary(self, group_id: str, episodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        start_tick = episodes[0].get("start_tick", 0)
        end_tick = episodes[-1].get("end_tick", 0)
        goals = [e.get("dominant_goal") for e in episodes if e.get("dominant_goal")]
        dom_goal = Counter(goals).most_common(1)[0][0] if goals else None
        qualities = [e.get("overall_quality", 1.0) for e in episodes]
        avg_quality = sum(qualities) / len(qualities) if qualities else 1.0
        episode_ids_str = [e.get("node_id", f"episode_{e.get('id', 0):06d}") for e in episodes]

        return {
            "hierarchy_id": group_id,
            "level": "group",
            "root_id": group_id,
            "episode_ids": episode_ids_str,
            "start_tick": start_tick,
            "end_tick": end_tick,
            "duration_ticks": end_tick - start_tick + 1,
            "dominant_signature": {"dominant_goal": dom_goal},
            "overall_quality": avg_quality,
        }
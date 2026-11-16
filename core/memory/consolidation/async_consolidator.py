from __future__ import annotations
from typing import List, Dict, Any, Optional
from collections import Counter
from .homeostasis_evaluator import HomeostasisEvaluator, HomeostasisConfig


class AsyncConsolidationManager:
    """
    Manages an in-memory staging queue for newly encoded episodes and runs 
    deferred background consolidation when the agent's homeostasis allows it[cite: 1].
    """
    def __init__(self, metadata_index, homeostasis_evaluator: Optional[HomeostasisEvaluator] = None, max_group_temporal_gap: int = 300):
        self.metadata_index = metadata_index
        self.homeostasis = homeostasis_evaluator or HomeostasisEvaluator()
        self.max_group_temporal_gap = max_group_temporal_gap
        
        # In-memory staging queue for unorganized/newly saved episode metadata
        self.staging_queue: List[Dict[str, Any]] = []

    def stage_episode(self, episode_meta: Dict[str, Any]) -> None:
        """Collects newly saved episode metadata into the staging queue without write-time blocking."""
        self.staging_queue.append(episode_meta)

    def tick(self, current_snapshot: Any, recent_prediction_error: float = 0.0) -> bool:
        """
        Evaluates homeostatic safety on each tick. If safe and items are staged,
        executes asynchronous background consolidation.
        """
        if not self.staging_queue:
            return False

        # Check if the agent is under high survival pressure or cognitive load
        if self.homeostasis.is_safe_for_consolidation(current_snapshot, recent_prediction_error):
            self.flush_and_consolidate()
            return True
            
        return False

    def flush_and_consolidate(self) -> None:
        """
        Batch-processes staged episodes into lazy high-level group summaries 
        and flushes them into the unified index storage[cite: 1].
        """
        if not self.staging_queue:
            return

        print(f"[AsyncConsolidation] Safe state detected. Consolidating {len(self.staging_queue)} staged episodes...")

        # Pull existing hierarchies from the unified index
        existing_hierarchies = self.metadata_index.data.get("hierarchies", {})
        
        # Process staged episodes into groups based on temporal proximity and goal/landmark continuity
        current_group_episodes = []
        
        for ep in self.staging_queue:
            if not current_group_episodes:
                current_group_episodes.append(ep)
                continue

            prev_ep = current_group_episodes[-1]
            same_goal = (prev_ep.get("dominant_goal") == ep.get("dominant_goal"))
            same_landmark = (prev_ep.get("nearest_landmark_id") == ep.get("nearest_landmark_id"))
            within_temporal_gap = (ep.get("start_tick", 0) - prev_ep.get("end_tick", 0)) <= self.max_group_temporal_gap

            if same_goal and (same_landmark or within_temporal_gap):
                current_group_episodes.append(ep)
            else:
                # Finalize current group and start a new one
                self._save_group_summary(current_group_episodes, existing_hierarchies)
                current_group_episodes = [ep]

        if current_group_episodes:
            self._save_group_summary(current_group_episodes, existing_hierarchies)

        # Clear staging queue after successful flush
        self.staging_queue.clear()
        
        # Save updated hierarchies back to the unified metadata index store
        self.metadata_index.update_hierarchies(existing_hierarchies)
        print("[AsyncConsolidation] Consolidation complete and unified index updated.")

    def _save_group_summary(self, episodes: List[Dict[str, Any]], hierarchies_dict: Dict[str, Any]) -> None:
        """Synthesizes a lightweight group summary object without duplicating raw telemetry[cite: 1]."""
        group_id = f"group_{len(hierarchies_dict) + 1:04d}"
        
        start_tick = episodes[0].get("start_tick", 0)
        end_tick = episodes[-1].get("end_tick", 0)
        
        goals = [e.get("dominant_goal") for e in episodes if e.get("dominant_goal")]
        skills = [e.get("dominant_skill") for e in episodes if e.get("dominant_skill")]
        
        dom_goal = Counter(goals).most_common(1)[0][0] if goals else None
        dom_skill = Counter(skills).most_common(1)[0][0] if skills else None
        
        qualities = [e.get("overall_quality", 1.0) for e in episodes]
        avg_quality = sum(qualities) / len(qualities) if qualities else 1.0

        episode_ids_str = [e.get("node_id", f"episode_{e.get('id', 0):06d}") for e in episodes]

        hierarchies_dict[group_id] = {
            "hierarchy_id": group_id,
            "level": "group",
            "root_id": group_id,
            "episode_ids": episode_ids_str,
            "start_tick": start_tick,
            "end_tick": end_tick,
            "duration_ticks": end_tick - start_tick + 1,
            "dominant_signature": {
                "dominant_goal": dom_goal,
                "dominant_skill": dom_skill,
            },
            "overall_quality": avg_quality,
        }
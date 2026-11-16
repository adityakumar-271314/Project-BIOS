from __future__ import annotations
from typing import List, Dict
from collections import Counter
from ..schemas import EpisodeMeta, LazyGroupSummary


class LazyGrouper:
    """Pure, stateless clustering utility that groups EpisodeMeta items by goal, landmark, and time."""

    def __init__(self, max_temporal_gap: int = 300):
        self.max_temporal_gap = max_temporal_gap

    def cluster(self, episodes: List[EpisodeMeta], start_index: int = 1, prefix: str = "group") -> Dict[str, LazyGroupSummary]:
        if not episodes:
            return {}

        groups: Dict[str, LazyGroupSummary] = {}
        current_cluster: List[EpisodeMeta] = []
        counter = start_index

        for ep in episodes:
            if not current_cluster:
                current_cluster.append(ep)
                continue

            prev = current_cluster[-1]
            same_goal = prev.dominant_goal == ep.dominant_goal
            same_landmark = (
                prev.nearest_landmark_id is not None
                and prev.nearest_landmark_id == ep.nearest_landmark_id
            )
            within_gap = (ep.start_tick - prev.end_tick) <= self.max_temporal_gap

            if same_goal and (same_landmark or within_gap):
                current_cluster.append(ep)
            else:
                gid = f"{prefix}_{counter:04d}"
                groups[gid] = self._summarize(gid, current_cluster)
                counter += 1
                current_cluster = [ep]

        if current_cluster:
            gid = f"{prefix}_{counter:04d}"
            groups[gid] = self._summarize(gid, current_cluster)

        return groups

    @staticmethod
    def _summarize(group_id: str, cluster: List[EpisodeMeta]) -> LazyGroupSummary:
        goals = [e.dominant_goal for e in cluster if e.dominant_goal]
        skills = [e.dominant_skill for e in cluster if e.dominant_skill]
        landmarks = [e.nearest_landmark_id for e in cluster if e.nearest_landmark_id is not None]

        dom_goal = Counter(goals).most_common(1)[0][0] if goals else None
        dom_skill = Counter(skills).most_common(1)[0][0] if skills else None
        dom_landmark = Counter(landmarks).most_common(1)[0][0] if landmarks else None
        avg_quality = sum(e.overall_quality for e in cluster) / len(cluster)

        return LazyGroupSummary(
            group_id=group_id,
            episode_ids=tuple(e.node_id for e in cluster),
            start_tick=cluster[0].start_tick,
            end_tick=cluster[-1].end_tick,
            dominant_goal=dom_goal,
            dominant_skill=dom_skill,
            nearest_landmark_id=dom_landmark,
            overall_quality=avg_quality,
        )
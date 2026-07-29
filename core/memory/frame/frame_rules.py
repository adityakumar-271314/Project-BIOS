from typing import Set
from ..schemas import TickSnapshot


class FrameRules:
    """Evaluates discrete event rules and triggers between consecutive snapshots."""

    def evaluate(
        self,
        prev: TickSnapshot,
        curr: TickSnapshot,
        config: any = None,
    ) -> Set[str]:
        tags: Set[str] = set()

        if not prev or not curr:
            return tags

        # --- Goal & Execution Transitions ---
        if prev.goal_name != curr.goal_name and curr.goal_name is not None:
            tags.add("goal_changed")
        if prev.active_skill != curr.active_skill:
            tags.add("skill_switched")
        if prev.target_type != curr.target_type or prev.target_id != curr.target_id:
            if curr.target_id is not None:
                tags.add("target_acquired")
            else:
                tags.add("target_lost")

        # --- Spatial & Environmental Transitions ---
        if prev.hazard_stim <= 0.2 and curr.hazard_stim > 0.2:
            tags.add("entered_hazard")
        elif prev.hazard_stim > 0.2 and curr.hazard_stim <= 0.2:
            tags.add("left_hazard")

        if curr.visible_food > prev.visible_food:
            tags.add("food_found")
        elif curr.visible_food < prev.visible_food:
            tags.add("food_lost")

        # --- Health & Reward Signals ---
        integrity_dmg_threshold = (
            getattr(config, "episodic_damage_threshold", 0.05) if config else 0.05
        )
        if (prev.integrity - curr.integrity) >= integrity_dmg_threshold:
            tags.add("damage_taken")

        food_rec_threshold = (
            getattr(config, "episodic_food_recovery_threshold", 0.1) if config else 0.1
        )
        if (curr.energy - prev.energy) >= food_rec_threshold:
            tags.add("food_eaten")

        return tags

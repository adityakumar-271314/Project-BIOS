from typing import Dict, Tuple
from ..schemas import TickSnapshot


class FrameChanges:
    """Detects continuous value shifts and categorical state transitions."""

    def compute(
        self,
        prev: TickSnapshot,
        curr: TickSnapshot,
    ) -> Tuple[Dict[str, bool], Dict[str, bool]]:
        change_mask: Dict[str, bool] = {}
        transition_flags: Dict[str, bool] = {}

        if not prev or not curr:
            return change_mask, transition_flags

        # Categorical state transitions
        transition_flags["goal_shift"] = prev.goal_name != curr.goal_name
        transition_flags["skill_shift"] = prev.active_skill != curr.active_skill
        transition_flags["action_shift"] = prev.action_state != curr.action_state
        transition_flags["target_shift"] = (
            prev.target_type != curr.target_type or prev.target_id != curr.target_id
        )

        # Continuous value change detection thresholds
        change_mask["pos_changed"] = (
            abs(curr.pos_x - prev.pos_x) > 0.1 or abs(curr.pos_y - prev.pos_y) > 0.1
        )
        change_mask["energy_changed"] = abs(curr.energy - prev.energy) > 0.01
        change_mask["integrity_changed"] = abs(curr.integrity - prev.integrity) > 0.001
        change_mask["stress_changed"] = abs(curr.stress - prev.stress) > 0.05
        change_mask["fear_changed"] = abs(curr.fear - prev.fear) > 0.05
        change_mask["drive_changed"] = abs(curr.drive - prev.drive) > 0.05
        change_mask["hazard_stim_changed"] = (
            abs(curr.hazard_stim - prev.hazard_stim) > 0.1
        )

        return change_mask, transition_flags

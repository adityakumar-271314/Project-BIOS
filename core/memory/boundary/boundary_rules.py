from typing import Dict, List, Tuple
from ..schemas import EpisodeFrame


class BoundaryRules:
    """
    Evaluates rich frame features between consecutive frames to detect evidence
    for episode start and end boundaries.
    """

    def evaluate(
        self,
        prev_frame: EpisodeFrame,
        curr_frame: EpisodeFrame,
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Evaluates trigger rules between consecutive annotated frames.

        Args:
            prev_frame: The preceding EpisodeFrame.
            curr_frame: The current EpisodeFrame being evaluated.

        Returns:
            A tuple of (start_triggers, end_triggers) mapping active trigger
            reason keys to their activation strength (0.0 to 1.0).
        """
        start_triggers: Dict[str, float] = {}
        end_triggers: Dict[str, float] = {}

        if not prev_frame or not curr_frame:
            return start_triggers, end_triggers

        prev_snap = prev_frame.snapshot
        curr_snap = curr_frame.snapshot

        # Extract rich annotations
        tags = curr_frame.event_tags
        transitions = curr_frame.transition_flags
        changes = curr_frame.change_mask

        # =====================================================================
        # START TRIGGERS
        # =====================================================================

        # 1. Goal changes
        if transitions.get("goal_shift") or "goal_changed" in tags:
            start_triggers["goal_change"] = 0.9

        # 2. Hazard entry
        if "entered_hazard" in tags:
            start_triggers["hazard_entry"] = 0.95
        elif curr_snap.hazard_stim > 0.3 and prev_snap.hazard_stim <= 0.3:
            start_triggers["hazard_entry"] = 0.8

        # 3. Interaction / Skill start
        if transitions.get("skill_shift") or "skill_switched" in tags:
            if curr_snap.active_skill and curr_snap.active_skill != "wander":
                start_triggers["interaction_start"] = 0.85

        # 4. Target acquisition
        if "target_acquired" in tags or (
            transitions.get("target_shift") and curr_snap.target_id is not None
        ):
            start_triggers["target_acquired"] = 0.85

        # 5. Emotion spikes
        fear_spike = curr_frame.fear_delta
        stress_spike = curr_frame.stress_delta
        if fear_spike > 0.2 or stress_spike > 0.2:
            intensity = min(1.0, max(fear_spike, stress_spike) / 0.4)
            start_triggers["emotion_spike"] = intensity

        # 6. Novel item / Food detection
        if "food_found" in tags:
            start_triggers["novel_item_detected"] = 0.75

        # 7. Importance or Surprise Spike
        if curr_frame.importance > 0.75 or curr_frame.prediction_error > 2.5:
            start_triggers["high_importance_spike"] = min(1.0, curr_frame.importance)

        # =====================================================================
        # END TRIGGERS
        # =====================================================================

        # 1. Goal resolution
        if prev_snap.goal_name is not None and curr_snap.goal_name is None:
            end_triggers["goal_resolution"] = 0.9

        # 2. Hazard exit
        if "left_hazard" in tags:
            end_triggers["hazard_exit"] = 0.95
        elif prev_snap.hazard_stim > 0.3 and curr_snap.hazard_stim <= 0.2:
            end_triggers["hazard_exit"] = 0.8

        # 3. Emotion stabilization
        if prev_snap.fear > 0.5 and curr_snap.fear <= 0.2:
            end_triggers["emotion_stabilization"] = 0.85
        elif prev_snap.stress > 0.5 and curr_snap.stress <= 0.25:
            end_triggers["emotion_stabilization"] = 0.75

        # 4. Activity completion / Action shift to idle
        if transitions.get("action_shift") and curr_snap.action_state in (None, "idle"):
            end_triggers["activity_completion"] = 0.7

        # 5. Target loss
        if "target_lost" in tags or (
            transitions.get("target_shift") and curr_snap.target_id is None
        ):
            end_triggers["target_loss"] = 0.8

        # 6. Drop in attention / importance after high activity
        if prev_frame.attention_score > 0.6 and curr_frame.attention_score < 0.2:
            end_triggers["attention_drop"] = 0.7

        return start_triggers, end_triggers

from dataclasses import dataclass


@dataclass
class Goal:
    name: str
    priority: float
    persistence: int = 0


class GoalStackManager:
    """
    Minimal Persistent Goal Selection Layer.

    Responsibilities:
        - Evaluate physiological/emotional pressures.
        - Maintain an active goal across frames.
        - Allow urgent goals to interrupt lower-priority goals.
        - Provide future compatibility for full stack behavior.
    """

    def __init__(self, brain_cfg, skill_cfg):

        self.cfg = brain_cfg
        self.skill_cfg = skill_cfg

        # Future compatibility: stack-based goal management
        self.goal_stack = []

        # Current active goal and its age (in ticks)
        self.active_goal = None
        self.goal_age = 0

    def evaluate_goal(self, ehe, sensor_data) -> Goal:
        """
        Main goal evaluation entrypoint.

        Behavior:
            - Continue current goal if still valid.
            - Otherwise select a new goal.
        """

        # Continue active goal if appropriate
        if self._should_keep_goal(ehe):
            self.goal_age += 1
            assert self.active_goal is not None
            return self.active_goal

        # Otherwise select a new goal
        new_goal: Goal = self._select_goal(ehe, sensor_data)

        # Debug hook / telemetry-friendly
        if (
            self.active_goal is None
            or self.active_goal.name != new_goal.name
        ):
            print(
                f"[GSM] Goal Change: "
                f"{self.active_goal.name if self.active_goal else 'None'} "
                f"-> {new_goal.name}"
            )

        self.active_goal = new_goal
        self.goal_age = 0

        return self.active_goal

    def _select_goal(self, ehe, sensor_data) -> Goal:
        """
        Select the highest-priority goal.
        """

        hazards_visible = any(
            obj.type == "hazard"
            for obj in sensor_data.sensed_objects
        )

        food_visible = any(
            obj.type == "food"
            for obj in sensor_data.sensed_objects
        )

        # HAZARD OVERRIDE
        if hazards_visible and ehe.fear > self.cfg.fear_threshold:
            return Goal(    
                name="avoid_hazard",
                priority=ehe.fear,
                persistence=self.skill_cfg.avoid_hazard.persistence,
            )

        # FOOD SEEKING
        if food_visible and ehe.drive > self.cfg.drive_threshold:
            return Goal(
                name="seek_food",
                priority=ehe.drive,
                persistence=self.skill_cfg.seek_food.persistence,
            )

        # DEFAULT WANDER
        return Goal(
            name="wander",
            persistence=self.skill_cfg.wander.persistence,
            priority=self.skill_cfg.wander.priority,
        )

    def _should_keep_goal(self, ehe) -> bool:
        """
        Determine whether the current goal should persist.
        """

        if self.active_goal is None:
            return False

        # Keep current goal while under persistence duration
        if (
            ehe.fear > self.cfg.fear_threshold
            and self.active_goal.name != "avoid_hazard"
        ):
            return False

        if self.goal_age < self.active_goal.persistence:

            # Hazard goals can terminate early if fear drops
            if self.active_goal.name == "avoid_hazard":
                return ehe.fear > (self.cfg.fear_threshold * 0.5)

            # Food seeking interrupted by strong fear
            if self.active_goal.name == "seek_food":
                return ehe.fear < self.cfg.fear_threshold

            # Wander persists naturally
            if self.active_goal.name == "wander":
                return True

        return False
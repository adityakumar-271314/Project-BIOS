"""
GoalStackManager (GSM) — Persistent Goal Arbitration with Memory Navigation Support.

Evaluates emotional and sensory state to select and maintain the current
behavioral goal (wander, seek_food, avoid_hazard) with persistence,
interruption, and geometric coordinate anchoring.
"""

from typing import Optional, List, Set, Tuple
from core.vector import Vector2
from core.brain.navigate.target import SpatialTargetTemplate
from core.brain.goal import Goal


class GoalStackManager:

    def __init__(self, brain_cfg, skill_cfg, memory_system):
        self.cfg = brain_cfg
        self.skill_cfg = skill_cfg
        self.memory_system = memory_system

        # Stack-based goal management
        self.goal_stack: List[Goal] = []

        # Current active goal and its age (in ticks)
        self.active_goal: Optional[Goal] = None
        self.goal_age: int = 0

        # Run-time runtime cache for bad target spots to prevent re-selection thrashing
        # Stores hashed tuple coordinates: (int(x), int(y))
        self._blacklisted_food_spots: Set[Tuple[int, int]] = set()
        self._memory_food_exhausted = False

    def evaluate_goal(
        self,
        ehe,
        sensor_data,
    ) -> Goal:
        """
        Main goal evaluation entrypoint.
        """
        memory_system = self.memory_system
        # 1. Check if the active goal should continue persisting
        if self._should_keep_goal(ehe):
            self.goal_age += 1
            assert self.active_goal is not None
            return self.active_goal

        # 2. If it shouldn't persist, manage interruptions or fetch a new goal
        new_goal: Goal = self._select_goal(
            ehe,
            sensor_data,
        )

        # 3. Interruption logic: If a high priority hazard overrides an incomplete memory search,
        # preserve the current spatial goal onto the stack so we can resume later.
        if (
            self.active_goal
            and self.active_goal.name == "seek_food"
            and new_goal.name == "avoid_hazard"
            and self.active_goal.status == "pending"
        ):
            if not any(g.name == "seek_food" for g in self.goal_stack):
                self.goal_stack.append(self.active_goal)

        # 4. If shifting back to normal and we have an interrupted goal, resume it
        if new_goal.name == "wander" and self.goal_stack:
            resumed_goal = self.goal_stack.pop()
            # Verify if resumed goal is spatial and hasn't been cleared/blacklisted
            if resumed_goal.spatial_target:
                spot_key = (
                    int(resumed_goal.spatial_target.target_vector.x),
                    int(resumed_goal.spatial_target.target_vector.y),
                )
                if spot_key not in self._blacklisted_food_spots:
                    new_goal = resumed_goal

        # 5. Apply telemetry print hooks
        if self.active_goal is None or self.active_goal.name != new_goal.name:
            print(
                f"[GSM] Goal Change: "
                f"{self.active_goal.name if self.active_goal else 'None'} "
                f"-> {new_goal.name} [{new_goal.strategy}]"
            )

        self.active_goal = new_goal
        self.goal_age = 0

        return self.active_goal

    def _select_goal(
        self,
        ehe,
        sensor_data,
    ) -> Goal:
        """
        Selects the highest priority goal and links spatial data if necessary.
        """
        hazards_visible = any(
            obj.type == "hazard" for obj in sensor_data.sensed_objects
        )
        food_visible = any(obj.type == "food" for obj in sensor_data.sensed_objects)

        # --- CRITICAL HAZARD OVERRIDE ---
        if hazards_visible and ehe.fear > self.cfg.fear_threshold:
            return Goal(
                name="avoid_hazard",
                priority=ehe.fear,
                persistence=self.skill_cfg.avoid_hazard.persistence,
                strategy="direct_sensory",
            )

        # --- FOOD SEEKING CORE DRIVE ---
        if ehe.drive > self.cfg.drive_threshold:
            if food_visible:
                self._memory_food_exhausted = False
                # Normal direct reactive targeting via live sensors
                return Goal(
                    name="seek_food",
                    priority=ehe.drive,
                    persistence=self.skill_cfg.seek_food.persistence,
                    strategy="direct_sensory",
                )
            elif self.memory_system is not None:

                if self._memory_food_exhausted:
                    return Goal(
                        name="wander",
                        persistence=self.skill_cfg.wander.persistence,
                        priority=self.skill_cfg.wander.priority,
                        strategy="direct_sensory",
                    )
                # Fallback to Episodic/Semantic Memory layout when blind
                food_memories = self.memory_system.recall_by_type("food_recovery")
                print(f"Food memories recalled: ", food_memories, end="")

                valid_memory = None

                for memory in reversed(food_memories):

                    spot_key = (
                        int(memory.peak_x),
                        int(memory.peak_y),
                    )

                    if spot_key in self._blacklisted_food_spots:
                        continue

                    valid_memory = memory
                    break

                if valid_memory is None:

                    self._memory_food_exhausted = True

                    print("[GSM] All remembered food locations exhausted.")

                else:

                    self._memory_food_exhausted = False

                    remembered_vector = Vector2(
                        valid_memory.peak_x,
                        valid_memory.peak_y,
                    )

                    target_template = SpatialTargetTemplate(
                        target_vector=remembered_vector,
                        hysteresis_radius=40.0,
                        confidence=getattr(
                            valid_memory,
                            "significance",
                            1.0,
                        )
                        / 10.0,
                    )

                    return Goal(
                        name="seek_food",
                        priority=ehe.drive,
                        persistence=self.skill_cfg.seek_food.persistence,
                        strategy="memory_nav",
                        spatial_target=target_template,
                        target_vector=remembered_vector,
                    )
        # --- DEFAULT WANDER ROUTINE ---
        return Goal(
            name="wander",
            persistence=self.skill_cfg.wander.persistence,
            priority=self.skill_cfg.wander.priority,
            strategy="direct_sensory",
        )

    def _should_keep_goal(self, ehe) -> bool:
        """
        Determine whether the current goal context should persist.
        """
        if self.active_goal is None:
            return False

        # Instantly interrupt anything if fear spikes and we are not handling a hazard
        if (
            ehe.fear > self.cfg.fear_threshold
            and self.active_goal.name != "avoid_hazard"
        ):
            return False

        if self.goal_age < self.active_goal.persistence:
            if self.active_goal.name == "avoid_hazard":
                return ehe.fear > (self.cfg.fear_threshold * 0.5)

            if self.active_goal.name == "seek_food":

                print(
                    "[GSM]",
                    self.active_goal.status,
                    self.goal_age,
                )
                # Ensure the current loop state hasn't flagged it complete or failed upstream
                if self.active_goal.status in ("done", "failed"):
                    return False
                return ehe.fear < self.cfg.fear_threshold

            if self.active_goal.name == "wander":
                return True

        return False

    def blacklist_target_coordinate(self, vector: Vector2):
        key = (int(vector.x), int(vector.y))
        self._blacklisted_food_spots.add(key)

        print(f"[GSM] Blacklisted food spot: " f"{key}")

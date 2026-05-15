"""
Episodic Memory System.

Encodes emotionally salient and statistically surprising
experiences into sparse autobiographical memories.
"""


from __future__ import annotations

import math
from typing import Dict, Optional
from .schemas import EpisodicEvent

class RunningStats:
    """
    Online mean/variance tracker using Welford's algorithm.

    Used to estimate what constitutes "normal" experience so the
    agent can detect statistically surprising state transitions.
    """

    def __init__(self):
        self.n = 0
        self.mean = 0.0
        self.M2 = 0.0

    def update(self, value: float) -> None:
        self.n += 1

        delta = value - self.mean
        self.mean += delta / self.n

        delta2 = value - self.mean
        self.M2 += delta * delta2

    @property
    def variance(self) -> float:
        if self.n < 2:
            return 0.0
        return self.M2 / (self.n - 1)

    @property
    def std(self) -> float:
        return math.sqrt(self.variance)


class EpisodicMemory:
    """
    Sparse autobiographical memory system.

    Encodes statistically surprising and emotionally salient events
    into compact episodic records.
    """

    def __init__(self, config):

        self.cfg = config
        self._was_critical_starving = False
        self._was_near_death = False

        # Stored episodic memories
        self.events: list[EpisodicEvent] = []

        # Internal tick counter
        self._tick = 0

        # Previous tick state snapshot
        self._last_state: Optional[Dict[str, float]] = None

        # Cooldown control
        self._last_event_tick = -999999

        # Online statistics trackers
        self._stats = {
            "energy_delta": RunningStats(),
            "integrity_delta": RunningStats(),
            "stress_delta": RunningStats(),
            "fear_delta": RunningStats(),
            "drive_delta": RunningStats(),
        }

    # Public API

    def update(
        self,
        sensors,
        body,
        emotions,
        semantic_memory,
    ) -> None:

        self._tick += 1

        current = self._snapshot_state(body, emotions)

        # Initialize baseline state
        if self._last_state is None:
            self._last_state = current
            return

        # 1. Compute state deltas

        deltas = {
            "energy_delta": current["energy"] - self._last_state["energy"],
            "integrity_delta": current["integrity"] - self._last_state["integrity"],
            "stress_delta": current["stress"] - self._last_state["stress"],
            "fear_delta": current["fear"] - self._last_state["fear"],
            "drive_delta": current["drive"] - self._last_state["drive"],
        }

        # 2. Compute statistical surprise

        weighted_surprise = (
            self._compute_surprise("energy_delta", deltas["energy_delta"]) * 0.2 +

            self._compute_surprise("integrity_delta", deltas["integrity_delta"],) * 0.3 +

            self._compute_surprise("stress_delta", deltas["stress_delta"],) * 0.2 +

            self._compute_surprise("fear_delta", deltas["fear_delta"],) * 0.2 +

            self._compute_surprise("drive_delta", deltas["drive_delta"],) * 0.1
        )

        # 3. Emotional weighting

        emotional_intensity = (
            emotions.stress * 0.3 +
            emotions.fear * 0.5 +
            emotions.drive * 0.2
        )

        significance = (
            weighted_surprise * 0.7 +
            emotional_intensity * 0.3
        )

        is_critical_starving = (
            body.energy <= self.cfg.critical_energy
        )

        is_near_death = (
            body.integrity <= self.cfg.near_death_integrity
        )

        if is_near_death and not self._was_near_death:

            event = EpisodicEvent(
                        tick=self._tick,
                        event_type="near_death",
                        significance=10.0,

                        pos_x=semantic_memory.position.x,
                        pos_y=semantic_memory.position.y,

                        energy=current["energy"],
                        integrity=current["integrity"],
                        stress=current["stress"],
                        fear=current["fear"],
                        drive=current["drive"],

                        energy_delta=deltas["energy_delta"],
                        integrity_delta=deltas["integrity_delta"],
                        stress_delta=deltas["stress_delta"],
                        fear_delta=deltas["fear_delta"],
                        drive_delta=deltas["drive_delta"],
                    )

            self.encode(event)
            self._last_event_tick = self._tick

        elif is_critical_starving and not self._was_critical_starving:

            event = EpisodicEvent(
                        tick=self._tick,
                        event_type="critical_starvation",
                        significance=8.0,

                        pos_x=semantic_memory.position.x,
                        pos_y=semantic_memory.position.y,

                        energy=current["energy"],
                        integrity=current["integrity"],
                        stress=current["stress"],
                        fear=current["fear"],
                        drive=current["drive"],

                        energy_delta=deltas["energy_delta"],
                        integrity_delta=deltas["integrity_delta"],
                        stress_delta=deltas["stress_delta"],
                        fear_delta=deltas["fear_delta"],
                        drive_delta=deltas["drive_delta"],
                    )

            self.encode(event)
            self._last_event_tick = self._tick

        self._was_near_death = is_near_death
        self._was_critical_starving = is_critical_starving

        # 4. Encode significant events

        cooldown = self.cfg.episodic_cooldown_ticks
        threshold = self.cfg.episodic_significance_threshold

        if (self._tick - self._last_event_tick) > cooldown:

            if significance >= threshold:

                event = EpisodicEvent(
                            tick=self._tick,
                            event_type=self._categorize_event(
                                deltas,
                                emotions,
                                sensors,
                            ),
                            significance=round(significance, 3),

                            pos_x=semantic_memory.position.x,
                            pos_y=semantic_memory.position.y,

                            energy=current["energy"],
                            integrity=current["integrity"],

                            stress=current["stress"],
                            fear=current["fear"],
                            drive=current["drive"],

                            energy_delta=deltas["energy_delta"],
                            integrity_delta=deltas["integrity_delta"],

                            stress_delta=deltas["stress_delta"],
                            fear_delta=deltas["fear_delta"],
                            drive_delta=deltas["drive_delta"],
                        )
                self.encode(event)
                self._last_event_tick = self._tick

        # 5. Update running statistics

        for key, value in deltas.items():
            self._stats[key].update(value)

        # 6. Finalize tick

        self._last_state = current

    # Internal helpers

    def _snapshot_state(self, body, emotions) -> Dict[str, float]:

        # Capture relevant physiological/emotional state.

        return {
            "energy": body.energy,
            "integrity": body.integrity,
            "stress": emotions.stress,
            "fear": emotions.fear,
            "drive": emotions.drive,
        }

    def _compute_surprise(
        self,
        key: str,
        value: float,
    ) -> float:
        
        # Compute z-score style surprise metric.

        stats = self._stats[key]

        # Wait until enough baseline data exists
        if stats.n < self.cfg.episodic_min_samples:
            return 0.0

        effective_std = max(
            stats.std,
            self.cfg.min_std,
        )

        return abs(value - stats.mean) / effective_std

    def _categorize_event(self, deltas, emotions, sensors) -> str:

        if deltas["integrity_delta"] < -self.cfg.episodic_damage_threshold:
            return "damage_spike"

        if deltas["energy_delta"] > self.cfg.episodic_food_recovery_threshold:
            return "food_recovery"

        if sensors.hazard_stim > 0.7:
            return "hazard_encounter"

        if emotions.fear > self.cfg.episodic_danger_fear_threshold:
            return "danger_state"

        if emotions.drive > self.cfg.episodic_starvation_drive_threshold:
            return "starvation_state"

        return "high_significance"

    def encode(self, event: EpisodicEvent) -> None:
        # Store episodic memory.

        self.events.append(event)
        print(
            f"[EPISODE] "
            f"type={event.event_type} "
            f"sig={event.significance:.2f}"
        )

    def debug_summary(self) -> str:
        return (
            f"[tick={self._tick}] "
            f"episodic_events={len(self.events)}"
        )
    def get_debug_memories(self) -> list[dict]:

        return [
            event.to_dict()
            for event in self.events[-100:]
        ]
    def export_state(self) -> dict:

        return {
            "tick": self._tick,
            "events": [
            event.to_dict()
            for event in self.events
        ],
    }

    def import_state(self, data: dict) -> None:

        self._tick = data.get("tick", 0)
        self.events = [
    EpisodicEvent.from_dict(event_data)
    for event_data in data.get("events", [])
]
    def get_events(self):

        return tuple(self.events)
# TODO: add degradation of memories and simplify configs.
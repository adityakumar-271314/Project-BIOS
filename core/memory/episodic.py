
from __future__ import annotations
import math
from .schemas import EpisodicEvent, EpisodeFrame, TickSnapshot
from .storage.serializer import EpisodeSerializer

"""
Episodic Memory System.

Encodes emotionally salient and statistically surprising
experiences into sparse autobiographical memories.

Online mean/variance tracker using Welford's algorithm.

Used to estimate what constitutes "normal" experience so the
agent can detect statistically surprising state transitions.
"""



class RunningStats:
    def __init__(self):
        self.n = 0
        self.mean = 0.0
        self.M2 = 0.0

    def update(self, value: float) -> None:
        self.n += 1
        delta = value - self.mean
        self.mean += delta / self.n
        self.M2 += delta * (value - self.mean)

    @property
    def variance(self) -> float:
        return self.M2 / (self.n - 1) if self.n > 1 else 0.0

    @property
    def std(self) -> float:
        return math.sqrt(self.variance)

class EpisodicMemory:
    def __init__(self, config):
        self.cfg = config
        self.events: list[EpisodicEvent] = []
        self._tick = 0
        self.serializer = EpisodeSerializer()

        self._stats = {
            "energy_delta": RunningStats(),
            "integrity_delta": RunningStats(),
            "stress_delta": RunningStats(),
            "fear_delta": RunningStats(),
            "drive_delta": RunningStats(),
        }

    def update(self) -> None:
        self._tick += 1

    def compute_surprise(self, key: str, value: float) -> float:
        stats = self._stats[key]
        if stats.n < self.cfg.episodic_min_samples:
            return 0.0
        effective_std = max(stats.std, self.cfg.min_std)
        return abs(value - stats.mean) / effective_std
    
    def compute_deltas(self, previous: TickSnapshot, current: TickSnapshot) -> dict:
        return {
            "energy_delta": current.energy - previous.energy,
            "integrity_delta": current.integrity - previous.integrity,
            "stress_delta": current.stress - previous.stress,
            "fear_delta": current.fear - previous.fear,
            "drive_delta": current.drive - previous.drive,
        }
    
    def compute_significance(self, deltas: dict, snapshot: TickSnapshot) -> float:
        weighted_surprise = (
            self.compute_surprise("energy_delta", deltas["energy_delta"]) * 0.2 +
            self.compute_surprise("integrity_delta", deltas["integrity_delta"]) * 0.3 +
            self.compute_surprise("stress_delta", deltas["stress_delta"]) * 0.2 +
            self.compute_surprise("fear_delta", deltas["fear_delta"]) * 0.2 +
            self.compute_surprise("drive_delta", deltas["drive_delta"]) * 0.1
        )
        emotional_intensity = (
            snapshot.stress * 0.3 + snapshot.fear * 0.5 + snapshot.drive * 0.2
        )
        return (weighted_surprise * 0.7) + (emotional_intensity * 0.3)

    def categorize_event(self, deltas: dict, snapshot: TickSnapshot) -> str:
        if deltas["integrity_delta"] < -self.cfg.episodic_damage_threshold:
            return "damage_spike"
        if deltas["energy_delta"] > self.cfg.episodic_food_recovery_threshold:
            return "food_recovery"
        if snapshot.hazard_stim > 0.7:
            return "hazard_encounter"
        if snapshot.fear > self.cfg.episodic_danger_fear_threshold:
            return "danger_state"
        if snapshot.drive > self.cfg.episodic_starvation_drive_threshold:
            return "starvation_state"
        return "high_significance"
    
    def update_stats(self, deltas: dict) -> None:
        for key, value in deltas.items():
            if key in self._stats:
                self._stats[key].update(value)

    def build_frame(self, previous_snapshot: TickSnapshot, current_snapshot: TickSnapshot) -> EpisodeFrame:
        """Called live every tick to process sensory transitions dynamically."""
        deltas = self.compute_deltas(previous_snapshot, current_snapshot)
        significance = self.compute_significance(deltas, current_snapshot)
        event_type = self.categorize_event(deltas=deltas, snapshot=current_snapshot)

        frame = EpisodeFrame(
            snapshot=current_snapshot,
            significance=significance,
            event_type=event_type,
            energy_delta=deltas["energy_delta"],
            integrity_delta=deltas["integrity_delta"],
            stress_delta=deltas["stress_delta"],
            fear_delta=deltas["fear_delta"],
            drive_delta=deltas["drive_delta"],
        )
        
        # Causal execution principle: Update statistical knowledge directly on creation
        self.update_stats(deltas)
        return frame

    def encode(self, event: EpisodicEvent) -> None:
        self.events.append(event)
        self.serializer.save(event)
        print(f"[EPISODE ENCODED] type={event.event_type} peak_sig={event.peak_significance:.2f} tick={event.peak_tick}")

    def get_events(self):
        return tuple(self.events)

    def export_state(self) -> dict:
        return {"tick": self._tick, "events": [e.to_dict() for e in self.events]}
       
    def import_state(self, data: dict) -> None:
        self._tick = data.get("tick", 0)
        self.events = [EpisodicEvent.from_dict(e) for e in data.get("events", [])]

    def get_debug_memories(self) -> list[dict]:
        return [e.to_dict() for e in self.events]

from .semantic import SemanticMemory
from .episodic import EpisodicMemory
from .temporal_buffer import TemporalBuffer
from .event_delay import EventDelayQueue
from .episode_pipeline import EpisodePipeline
from pathlib import Path

class MemorySystem:

    def __init__(self, config):
        self.cfg = config
        self.semantic = SemanticMemory(config)
        self.episodic = EpisodicMemory(config)
        self.temporal_buffer = TemporalBuffer(
            seconds=15,
            fps=60,
        )
        self.event_delay = EventDelayQueue(delay_ticks=180)
        self.pipeline = EpisodePipeline(
            episodic_memory=self.episodic,
            temporal_buffer=self.temporal_buffer,
        )
        self._tick = 0

    def update(self, sensors, body, emotions, active_goal, active_skill, target):
        self._tick += 1
        self.semantic.update(sensors)
        self.temporal_buffer.capture(
            tick=self._tick,
            sensors=sensors,
            body=body,
            emotions=emotions,
            semantic_memory=self.semantic,
            goal=active_goal,
            active_skill=active_skill,
            target=target,
        )
        latest_snapshot = self.temporal_buffer.latest()
        snapshots = self.temporal_buffer.snapshots()

        if len(snapshots) >= 2:
            previous_snapshot = snapshots[-2]
            frame = self.episodic.build_frame(previous_snapshot, latest_snapshot)
            self.temporal_buffer.append_frame(frame)

            if frame.event_type != "high_significance" or frame.significance > getattr(
                self.cfg, "episodic_significance_threshold", 4.0
            ):
                if not self.event_delay._pending or (
                    self._tick - self.event_delay._pending[-1] > 300
                ):
                    self.mark_candidate_event(self._tick)

        self.episodic.update()

        ready_events = self.event_delay.get_ready(self._tick)
        for candidate_tick in ready_events:
            episodes = self.pipeline.process_candidate(candidate_tick)
            for episode in episodes:
                # --- Use high-speed index checking rather than RAM list iterations ---
                if not any(
                    e["peak_tick"] == episode.peak_tick 
                    for e in self.episodic.archive.index.data["episodes"]
                ):
                    self.episodic.encode(episode)

    def import_state(self, data: dict) -> None:

        self.semantic.import_state(data.get("semantic", {}))

        self.episodic.import_state(data.get("episodic", {}))

    def export_state(self) -> dict:

        return {
            "semantic": self.semantic.export_state(),
            "episodic": self.episodic.export_state(),
            "version": 1,
        }

    def recent_snapshots(
        self,
        seconds: float = 5.0,
    ):
        return self.temporal_buffer.recent_seconds(seconds)

    def snapshot_context(
        self,
        center_tick: int,
        before_ticks: int,
        after_ticks: int,
    ):
        return self.temporal_buffer.get_context(
            center_tick=center_tick,
            before_ticks=before_ticks,
            after_ticks=after_ticks,
        )

    def latest_snapshot(self):
        return self.temporal_buffer.latest()

    def mark_candidate_event(
        self,
        tick: int,
    ):
        self.event_delay.add_candidate(tick)

    def get_ready_events(self):
        return self.event_delay.get_ready(self._tick)

    def get_spatial_bias(self, position=None, radius=None):
        return self.semantic.get_spatial_bias(
            position=position,
            radius=radius,
        )

    def get_debug_memories(self):
        return self.episodic.get_debug_memories()

    @property
    def position(self):

        return self.semantic.position

    @property
    def velocity(self):

        return self.semantic.velocity

    @property
    def landmarks(self):

        return self.semantic.landmarks

    @property
    def internal_pos(self):
        return self.semantic.internal_pos

    @property
    def internal_vel(self):
        return self.semantic.internal_vel

    @property
    def internal_heading(self) -> float:
        return self.semantic.internal_heading

    def recall_recent(self, limit: int = 10):
        meta_matches = self.episodic.archive.index.query_recent(limit)
        return [self.episodic.archive.load(m["id"]) for m in meta_matches]

    def recall_by_type(self, event_type: str, limit: int | None = None):
        meta_matches = self.episodic.archive.index.query_by_type(event_type, limit)
        return [self.episodic.archive.load(m["id"]) for m in meta_matches]

    def recall_significant(self, min_significance: float = 5.0):
        return [
            self.episodic.archive.load(m["id"])
            for m in self.episodic.archive.index.data["episodes"]
            if m["peak_significance"] >= min_significance
        ]

    def recall_near(self, pos_x: float, pos_y: float, radius: float):
        return self.episodic.archive.recall_near(pos_x, pos_y, radius)

    def recall_latest(self):
        return self.episodic.archive.recall_latest()

    def last_significant_event(self, min_significance: float = 5.0):
        matches = [
            m for m in self.episodic.archive.index.data["episodes"]
            if m["peak_significance"] >= min_significance
        ]
        return self.episodic.archive.load(matches[-1]["id"]) if matches else None

    def last_danger_event(self):
        danger_types = {"danger_state", "hazard_encounter", "damage_spike", "near_death"}
        matches = [
            m for m in self.episodic.archive.index.data["episodes"]
            if m["event_type"] in danger_types
        ]
        return self.episodic.archive.load(matches[-1]["id"]) if matches else None

    def last_food_recovery(self):
        matches = self.episodic.archive.index.query_by_type("food_recovery", limit=1)
        return self.episodic.archive.load(matches[-1]["id"]) if matches else None

    def most_significant_event(self):
        episodes = self.episodic.archive.index.data["episodes"]
        if not episodes:
            return None
        target_meta = max(episodes, key=lambda m: m["peak_significance"])
        return self.episodic.archive.load(target_meta["id"])

    def nearby_danger_memories(self, pos_x: float, pos_y: float, radius: float):
        danger_types = {"danger_state", "hazard_encounter", "damage_spike", "near_death"}
        nearby = self.recall_near(pos_x=pos_x, pos_y=pos_y, radius=radius)
        return [event for event in nearby if event.event_type in danger_types]

    def initialize_run_state(
            self,
            continuation: bool,
            storage_path: str = "spatial_memory_state.json",
            episodes_dir: Path | str | None = None,
        ) -> None:
            # Pass spatial memory path to semantic memory
            self.semantic.initialize_run_state(continuation, storage_path)
            
            # Pass run episode directory to episodic memory
            self.episodic.initialize_run_state(continuation, episodes_dir)
            
            if continuation:
                self._tick = self.semantic._tick
                self.temporal_buffer.clear()
            else:
                self._tick = 0
    def shutdown_and_save(
        self,
        storage_path: str = "spatial_memory_state.json",
    ) -> None:
        self.semantic.shutdown_and_save(storage_path)

    def reset_state(
            self,
            storage_path: str = "spatial_memory_state.json",
            episodes_dir: Path | str | None = None,
        ) -> None:
            self.semantic.reset_state(storage_path)
            self.episodic.initialize_run_state(continuation=False, episodes_dir=episodes_dir)
from pathlib import Path
from typing import Optional, Any, List, Dict

from .spatial_memory.core import SpatialMemory
from .episodic import EpisodicMemory
from .event_delay import EventDelayQueue
from .episode_pipeline import EpisodePipeline
from .boundary.boundary_detector import BoundaryDetector
from .schemas import EpisodeCandidate
from .temporal.temporal_buffer import TemporalBuffer
from .temporal.annotation_queue import AnnotationQueue
from .frame.frame_annotator import FrameAnnotator
from .frame.candidate_scorer import EpisodeCandidateScorer


class MemorySystem:
    """
    Central orchestrator for spatial, transient streaming, 
    rich frame annotation, candidate scoring, boundary detection, and long-term episodic memory.
    """

    def __init__(self, config):
        self.cfg = config
        
        self.spatial_mem = SpatialMemory(config)
        self.episodic = EpisodicMemory(config)
        
        self.temporal_buffer = TemporalBuffer(seconds=15, fps=60)
        self.annotation_queue = AnnotationQueue(delay_ticks=0)
        self.frame_annotator = FrameAnnotator(config=config)
        self.candidate_scorer = EpisodeCandidateScorer(config=config)  # NEW
        self.boundary_detector = BoundaryDetector()
        
        self.event_delay = EventDelayQueue(delay_ticks=180)
        self.pipeline = EpisodePipeline(
            episodic_memory=self.episodic,
            temporal_buffer=self.temporal_buffer,
            boundary_detector=self.boundary_detector,
        )

        self._tick = 0
        self._last_annotated_snapshot = None

    def update(
        self,
        sensors: Any,
        body: Any,
        emotions: Any,
        active_goal: Any,
        active_skill: Any,
        target: Any,
    ) -> None:
        self._tick += 1

        # Update Spatial Memory
        self.spatial_mem.update(sensors)

        # Capture raw TickSnapshot into Temporal Buffer & Annotation Queue
        snapshot = self.temporal_buffer.capture(
            tick=self._tick,
            sensors=sensors,
            body=body,
            emotions=emotions,
            spatial_mem=self.spatial_mem,
            goal=active_goal,
            active_skill=active_skill,
            target=target,
        )
        self.annotation_queue.enqueue(snapshot)

        # Process ready snapshots through FrameAnnotator pipeline
        ready_snapshots = self.annotation_queue.pop_ready(self._tick)
        for curr_snapshot in ready_snapshots:
            # Annotate Frame
            frame = self.frame_annotator.annotate(
                prev_snapshot=self._last_annotated_snapshot,
                curr_snapshot=curr_snapshot,
                stats=self.episodic.stats,
            )

            # Causal update of Welford running statistics
            self.episodic.update_stats(
                {
                    "energy_delta": frame.energy_delta,
                    "integrity_delta": frame.integrity_delta,
                    "stress_delta": frame.stress_delta,
                    "fear_delta": frame.fear_delta,
                    "drive_delta": frame.drive_delta,
                }
            )

            # Store Frame in Temporal Buffer
            self.temporal_buffer.append_frame(frame)
            self._last_annotated_snapshot = curr_snapshot

            # Compute continuous candidate score and rolling attention
            candidate = self.candidate_scorer.process(frame)

            # Trigger candidate event using rolling score threshold
            candidate_thresh = getattr(self.cfg, "candidate_threshold", 0.8)
            if candidate.rolling_score > candidate_thresh:
                if not self.event_delay._pending or (
                    self._tick - self.event_delay._pending[-1].tick > 300
                ):
                    self.mark_candidate_event(candidate)

        # Advance Episodic Memory Clock
        self.episodic.update()

        # Process Retrospective Delay Queue through Pipeline
        ready_candidates = self.event_delay.get_ready(self._tick)
        for candidate in ready_candidates:
            candidate_tick = candidate.tick if hasattr(candidate, "tick") else candidate
            episodes = self.pipeline.process_candidate(candidate_tick)
            for episode in episodes:
                if not any(
                    e["peak_tick"] == episode.peak_tick
                    for e in self.episodic.archive.index.data["episodes"]
                ):
                    self.episodic.encode(episode)
        
    def mark_candidate_event(self, candidate: EpisodeCandidate) -> None:
        self.event_delay.add_candidate(candidate)

    def initialize_run_state(
        self,
        continuation: bool,
        storage_path: str = "spatial_memory_state.json",
        episodes_dir: Path | str | None = None,
    ) -> None:
        self.spatial_mem.initialize_run_state(continuation, storage_path)
        self.episodic.initialize_run_state(continuation, episodes_dir)

        if continuation:
            self._tick = self.spatial_mem._tick
            self.temporal_buffer.clear()
            self.annotation_queue.clear()
            self._last_annotated_snapshot = None
        else:
            self._tick = 0
            self._last_annotated_snapshot = None

    def import_state(self, data: dict) -> None:
        self.spatial_mem.import_state(data.get("semantic", {}))
        self.episodic.import_state(data.get("episodic", {}))

    def export_state(self) -> dict:
        return {
            "semantic": self.spatial_mem.export_state(),
            "episodic": self.episodic.export_state(),
            "version": 1,
        }

    def shutdown_and_save(self, storage_path: str = "spatial_memory_state.json") -> None:
        self.spatial_mem.shutdown_and_save(storage_path)

    def reset_state(
        self,
        storage_path: str = "spatial_memory_state.json",
        episodes_dir: Path | str | None = None,
    ) -> None:
        self.spatial_mem.reset_state(storage_path)
        self.episodic.initialize_run_state(continuation=False, episodes_dir=episodes_dir)
        self.temporal_buffer.clear()
        self.annotation_queue.clear()
        self._last_annotated_snapshot = None

    # --- Query & Accessor Proxies ---

    def recent_snapshots(self, seconds: float = 5.0):
        return self.temporal_buffer.recent_seconds(seconds)

    def snapshot_context(self, center_tick: int, before_ticks: int, after_ticks: int):
        return self.temporal_buffer.get_context(
            center_tick=center_tick,
            before_ticks=before_ticks,
            after_ticks=after_ticks,
        )

    def latest_snapshot(self):
        return self.temporal_buffer.latest()

    def get_ready_events(self):
        return self.event_delay.get_ready(self._tick)

    def get_spatial_bias(self, position=None, radius=None):
        return self.spatial_mem.get_spatial_bias(position=position, radius=radius)

    def get_debug_memories(self):
        return self.episodic.get_debug_memories()

    @property
    def position(self):
        return self.spatial_mem.position

    @property
    def velocity(self):
        return self.spatial_mem.velocity

    @property
    def landmarks(self):
        return self.spatial_mem.landmarks

    @property
    def internal_pos(self):
        return self.spatial_mem.internal_pos

    @property
    def internal_vel(self):
        return self.spatial_mem.internal_vel

    @property
    def internal_heading(self) -> float:
        return self.spatial_mem.internal_heading

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
            m
            for m in self.episodic.archive.index.data["episodes"]
            if m["peak_significance"] >= min_significance
        ]
        return self.episodic.archive.load(matches[-1]["id"]) if matches else None

    def last_danger_event(self):
        danger_types = {
            "danger_state",
            "hazard_encounter",
            "damage_spike",
            "near_death",
        }
        matches = [
            m
            for m in self.episodic.archive.index.data["episodes"]
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
        danger_types = {
            "danger_state",
            "hazard_encounter",
            "damage_spike",
            "near_death",
        }
        nearby = self.recall_near(pos_x=pos_x, pos_y=pos_y, radius=radius)
        return [event for event in nearby if event.event_type in danger_types]
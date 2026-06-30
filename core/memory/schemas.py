from dataclasses import dataclass, field, asdict
from typing import List
# RAW TEMPORAL DATA

@dataclass(slots=True)
class TickSnapshot:

    tick: int
    pos_x: float
    pos_y: float
    vel_x: float
    vel_y: float
    heading: float
    energy: float
    integrity: float
    stress: float
    fear: float
    drive: float
    goal_name: str | None = None
    goal_priority: float = 0.0
    active_skill: str | None = None
    action_state: str | None = None
    target_type: str | None = None
    target_id: int | None = None
    target_x: float | None = None
    target_y: float | None = None
    visible_food: int = 0
    visible_hazards: int = 0
    visible_landmarks: int = 0
    hazard_stim: float = 0.0
    food_stim: float = 0.0
    notes: str | None = None


# TRANSIENT FRAME

@dataclass(slots=True)
class EpisodeFrame:

    snapshot: TickSnapshot
    significance: float
    event_type: str
    energy_delta: float
    integrity_delta: float
    stress_delta: float
    fear_delta: float
    drive_delta: float

# Lightweight key frame for compression
@dataclass(slots=True)
class SparseFrame:
    """Conservative sparse representation - keeps most useful fields"""
    tick: int
    pos_x: float
    pos_y: float
    vel_x: float
    vel_y: float
    heading: float
    energy: float
    integrity: float
    stress: float
    fear: float
    drive: float
    significance: float
    active_skill: str | None = None
    action_state: str | None = None
    target_type: str | None = None
    visible_food: int = 0
    visible_hazards: int = 0
    notes: str | None = None

# PERSISTENT EPISODE - conservative update
@dataclass(slots=True)
class EpisodicEvent:
    start_tick: int
    peak_tick: int
    end_tick: int
    event_type: str
    peak_significance: float
    start_x: float
    start_y: float
    peak_x: float
    peak_y: float
    end_x: float
    end_y: float
    max_fear: float
    avg_fear: float
    max_stress: float
    avg_stress: float
    max_drive: float
    avg_drive: float
    energy_delta: float
    integrity_delta: float
    peak_snapshot: TickSnapshot
    
    # === Storage compression change only ===
    key_frames: List[SparseFrame] = field(default_factory=list)
    
    notes: str | None = None   # kept for flexibility

    def to_dict(self):
        return {
            "start_tick": self.start_tick,
            "peak_tick": self.peak_tick,
            "end_tick": self.end_tick,
            "event_type": self.event_type,
            "peak_significance": self.peak_significance,
            "start_position": {"x": self.start_x, "y": self.start_y},
            "peak_position": {"x": self.peak_x, "y": self.peak_y},
            "end_position": {"x": self.end_x, "y": self.end_y},
            "state": {
                "max_fear": self.max_fear,
                "avg_fear": self.avg_fear,
                "max_stress": self.max_stress,
                "avg_stress": self.avg_stress,
                "max_drive": self.max_drive,
                "avg_drive": self.avg_drive,
            },
            "deltas": {
                "energy_delta": self.energy_delta,
                "integrity_delta": self.integrity_delta,
            },
            "peak_snapshot": asdict(self.peak_snapshot),
            "key_frames": [asdict(kf) for kf in self.key_frames],
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'EpisodicEvent':
        state = data.get("state", {})
        deltas = data.get("deltas", {})
        start_pos = data.get("start_position", {"x": 0, "y": 0})
        peak_pos = data.get("peak_position", {"x": 0, "y": 0})
        end_pos = data.get("end_position", {"x": 0, "y": 0})
        
        peak_snap_data = data.get("peak_snapshot")
        peak_snap = TickSnapshot(**peak_snap_data) if isinstance(peak_snap_data, dict) else peak_snap_data

        raw_key_frames = data.get("key_frames", [])
        key_frames = [SparseFrame(**kf) if isinstance(kf, dict) else kf for kf in raw_key_frames]

        return cls(
            start_tick=data["start_tick"],
            peak_tick=data["peak_tick"],
            end_tick=data["end_tick"],
            event_type=data["event_type"],
            peak_significance=data["peak_significance"],
            start_x=start_pos["x"],
            start_y=start_pos["y"],
            peak_x=peak_pos["x"],
            peak_y=peak_pos["y"],
            end_x=end_pos["x"],
            end_y=end_pos["y"],
            max_fear=state.get("max_fear", 0.0),
            avg_fear=state.get("avg_fear", 0.0),
            max_stress=state.get("max_stress", 0.0),
            avg_stress=state.get("avg_stress", 0.0),
            max_drive=state.get("max_drive", 0.0),
            avg_drive=state.get("avg_drive", 0.0),
            energy_delta=deltas.get("energy_delta", 0.0),
            integrity_delta=deltas.get("integrity_delta", 0.0),
            peak_snapshot=peak_snap,
            key_frames=key_frames,
            notes=data.get("notes")
        )
    
@dataclass(slots=True)
class ReconstructedTick:
    tick: int

    pos_x: float
    pos_y: float

    vel_x: float
    vel_y: float

    heading: float

    energy: float
    integrity: float

    stress: float
    fear: float
    drive: float

    confidence: float = 1.0
    anchor: bool = False
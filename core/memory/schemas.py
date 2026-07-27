from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Set, Dict, Any

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


# TRANSIENT FRAME (EXPANDED FOR PART A)


@dataclass(slots=True)
class EpisodeFrame:

    snapshot: TickSnapshot
    
    # Legacy / Bridge Fields (Kept for compatibility with downstream EpisodeBuilder)
    significance: float
    event_type: str
    
    # Deltas
    energy_delta: float
    integrity_delta: float
    stress_delta: float
    fear_delta: float
    drive_delta: float

    # Rich Metrics (Part A)
    importance: float = 0.0
    prediction_error: float = 0.0
    attention_score: float = 0.0
    novelty: float = 0.0

    # Categorical Signals & Change Masks (Part A)
    event_tags: Set[str] = field(default_factory=set)
    transition_flags: Dict[str, bool] = field(default_factory=dict)
    change_mask: Dict[str, bool] = field(default_factory=dict)


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

@dataclass(slots=True, frozen=True)
class StateSummary:
    """Compact summary of continuous metrics (initial, final, min, max, net delta)."""
    initial: float
    final: float
    min_val: float
    max_val: float

    @property
    def net_change(self) -> float:
        return self.final - self.initial


@dataclass(slots=True, frozen=True)
class BehavioralTransition:
    """Captures a meaningful state shift without storing telemetry."""
    tick: int
    from_state: str | None
    to_state: str | None


@dataclass(slots=True, frozen=True)
class EpisodeSignature:
    """
    Canonical, language-agnostic behavioral representation of an episode.
    Immutable once finalized. Captures identity, outcome, and importance drivers
    without duplicating detailed frame telemetry or keyframes.
    """
    # Behavioral Identity
    dominant_goal: str | None = None
    dominant_skill: str | None = None
    dominant_target: str | None = None

    # Meaningful Transitions (Only populated if state changes occurred)
    goal_transitions: Tuple[BehavioralTransition, ...] = ()
    skill_transitions: Tuple[BehavioralTransition, ...] = ()
    target_transitions: Tuple[BehavioralTransition, ...] = ()

    # Outcome & Summaries
    outcome_completed: bool = False
    resource_summaries: Dict[str, StateSummary] = field(default_factory=dict)
    emotion_summaries: Dict[str, StateSummary] = field(default_factory=dict)

    # Environment Summary
    max_hazard_exposure: float = 0.0
    max_reward_exposure: float = 0.0
    landmark_interactions: int = 0

    # Retention Drivers & Descriptors (Why this episode exists)
    primary_importance_drivers: Tuple[str, ...] = ()
    duration_ticks: int = 0
    behavioral_complexity: float = 0.0
    overall_novelty: float = 0.0
    overall_importance: float = 0.0

    # Lightweight Keyframe References (Tick identifiers only)
    keyframe_ticks: Tuple[int, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dominant_goal": self.dominant_goal,
            "dominant_skill": self.dominant_skill,
            "dominant_target": self.dominant_target,
            "goal_transitions": [asdict(t) for t in self.goal_transitions],
            "skill_transitions": [asdict(t) for t in self.skill_transitions],
            "target_transitions": [asdict(t) for t in self.target_transitions],
            "outcome_completed": self.outcome_completed,
            "resource_summaries": {k: asdict(v) for k, v in self.resource_summaries.items()},
            "emotion_summaries": {k: asdict(v) for k, v in self.emotion_summaries.items()},
            "max_hazard_exposure": self.max_hazard_exposure,
            "max_reward_exposure": self.max_reward_exposure,
            "landmark_interactions": self.landmark_interactions,
            "primary_importance_drivers": list(self.primary_importance_drivers),
            "duration_ticks": self.duration_ticks,
            "behavioral_complexity": self.behavioral_complexity,
            "overall_novelty": self.overall_novelty,
            "overall_importance": self.overall_importance,
            "keyframe_ticks": list(self.keyframe_ticks),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EpisodeSignature":
        if not data:
            return cls()
        return cls(
            dominant_goal=data.get("dominant_goal"),
            dominant_skill=data.get("dominant_skill"),
            dominant_target=data.get("dominant_target"),
            goal_transitions=tuple(BehavioralTransition(**t) for t in data.get("goal_transitions", [])),
            skill_transitions=tuple(BehavioralTransition(**t) for t in data.get("skill_transitions", [])),
            target_transitions=tuple(BehavioralTransition(**t) for t in data.get("target_transitions", [])),
            outcome_completed=data.get("outcome_completed", False),
            resource_summaries={k: StateSummary(**v) for k, v in data.get("resource_summaries", {}).items()},
            emotion_summaries={k: StateSummary(**v) for k, v in data.get("emotion_summaries", {}).items()},
            max_hazard_exposure=data.get("max_hazard_exposure", 0.0),
            max_reward_exposure=data.get("max_reward_exposure", 0.0),
            landmark_interactions=data.get("landmark_interactions", 0),
            primary_importance_drivers=tuple(data.get("primary_importance_drivers", ())),
            duration_ticks=data.get("duration_ticks", 0),
            behavioral_complexity=data.get("behavioral_complexity", 0.0),
            overall_novelty=data.get("overall_novelty", 0.0),
            overall_importance=data.get("overall_importance", 0.0),
            keyframe_ticks=tuple(data.get("keyframe_ticks", ())),
        )

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

    # Storage compression change
    key_frames: List[SparseFrame] = field(default_factory=list)
    
    # Immutable Canonical Behavioral Signature
    signature: EpisodeSignature = field(default_factory=EpisodeSignature)

    notes: str | None = None  # Kept as optional secondary text view

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
            "signature": self.signature.to_dict(),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EpisodicEvent":
        state = data.get("state", {})
        deltas = data.get("deltas", {})
        start_pos = data.get("start_position", {"x": 0, "y": 0})
        peak_pos = data.get("peak_position", {"x": 0, "y": 0})
        end_pos = data.get("end_position", {"x": 0, "y": 0})

        peak_snap_data = data.get("peak_snapshot")
        peak_snap = (
            TickSnapshot(**peak_snap_data)
            if isinstance(peak_snap_data, dict)
            else peak_snap_data
        )

        raw_key_frames = data.get("key_frames", [])
        key_frames = [
            SparseFrame(**kf) if isinstance(kf, dict) else kf for kf in raw_key_frames
        ]
        
        sig_data = data.get("signature", {})
        signature = EpisodeSignature.from_dict(sig_data) if isinstance(sig_data, dict) else sig_data

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
            signature=signature,
            notes=data.get("notes"),
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

@dataclass(slots=True)
class EpisodeCandidate:
    """Continuous multi-signal candidate event produced by rolling attention."""

    tick: int
    frame_score: float
    rolling_score: float
    confidence: float
    contributors: Dict[str, float] = field(default_factory=dict)
    peak_reason: str = ""
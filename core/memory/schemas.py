from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Set, Dict, Any, Optional

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


@dataclass(slots=True, frozen=True)
class CompressionMetadata:
    """Immutable metrics describing the episode frame compression process."""

    compression_ratio: float = 0.0
    original_keyframe_count: int = 0
    compressed_keyframe_count: int = 0
    information_density: float = 0.0
    compression_strategy: str = "anchor_pruning"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "compression_ratio": self.compression_ratio,
            "original_keyframe_count": self.original_keyframe_count,
            "compressed_keyframe_count": self.compressed_keyframe_count,
            "information_density": self.information_density,
            "compression_strategy": self.compression_strategy,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompressionMetadata":
        if not data:
            return cls()
        return cls(
            compression_ratio=data.get("compression_ratio", 0.0),
            original_keyframe_count=data.get("original_keyframe_count", 0),
            compressed_keyframe_count=data.get("compressed_keyframe_count", 0),
            information_density=data.get("information_density", 0.0),
            compression_strategy=data.get("compression_strategy", "anchor_pruning"),
        )


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


class SpatialEntityType(str, Enum):
    LANDMARK = "landmark"
    FOOD_PATCH = "food_patch"
    HAZARD_ZONE = "hazard_zone"


@dataclass(slots=True, frozen=True)
class SpatialContextReference:
    """Lightweight reference to a nearby or interacting spatial entity or stimulus zone for a keyframe."""

    entity_type: SpatialEntityType
    pos_x: float
    pos_y: float
    entity_id: int | str | None = None
    intensity: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_type": (
                self.entity_type.value
                if isinstance(self.entity_type, Enum)
                else self.entity_type
            ),
            "pos_x": self.pos_x,
            "pos_y": self.pos_y,
            "entity_id": self.entity_id,
            "intensity": self.intensity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpatialContextReference":
        if not data:
            return cls(entity_type=SpatialEntityType.LANDMARK, pos_x=0.0, pos_y=0.0)
        raw_type = data.get("entity_type", SpatialEntityType.LANDMARK.value)
        try:
            entity_type = SpatialEntityType(raw_type)
        except ValueError:
            entity_type = SpatialEntityType.LANDMARK
        return cls(
            entity_type=entity_type,
            pos_x=data.get("pos_x", 0.0),
            pos_y=data.get("pos_y", 0.0),
            entity_id=data.get("entity_id"),
            intensity=data.get("intensity", 0.0),
        )


@dataclass(slots=True)
class SparseFrame:
    """Streamlined conservative sparse representation - retains core kinematics, vitals, and spatial context."""

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
    spatial_context: Tuple[SpatialContextReference, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["spatial_context"] = [
            sc.to_dict() if hasattr(sc, "to_dict") else sc
            for sc in self.spatial_context
        ]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SparseFrame":
        if not data:
            return cls(
                tick=0,
                pos_x=0.0,
                pos_y=0.0,
                vel_x=0.0,
                vel_y=0.0,
                heading=0.0,
                energy=0.0,
                integrity=0.0,
                stress=0.0,
                fear=0.0,
                drive=0.0,
                significance=0.0,
            )
        sc_data = data.get("spatial_context", [])
        return cls(
            tick=data.get("tick", 0),
            pos_x=data.get("pos_x", 0.0),
            pos_y=data.get("pos_y", 0.0),
            vel_x=data.get("vel_x", 0.0),
            vel_y=data.get("vel_y", 0.0),
            heading=data.get("heading", 0.0),
            energy=data.get("energy", 0.0),
            integrity=data.get("integrity", 0.0),
            stress=data.get("stress", 0.0),
            fear=data.get("fear", 0.0),
            drive=data.get("drive", 0.0),
            significance=data.get("significance", 0.0),
            spatial_context=tuple(
                SpatialContextReference.from_dict(sc) for sc in sc_data
            ),
        )


class OutcomeStatus(str, Enum):
    """Qualitative outcome categories for an episodic event."""

    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ABORTED = "aborted"
    UNKNOWN = "unknown"


@dataclass(slots=True, frozen=True)
class MacroTransition:
    """Captures a significant macro behavioral shift (milestone) without storing tick-level noise."""

    from_state: str | None
    to_state: str | None
    transition_type: str  # "goal", "skill", or "target"


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
class EpisodeSignature:
    """
    Canonical, language-agnostic behavioral representation of an episode.
    Immutable once finalized. Captures identity, outcome, spatial context, and
    importance drivers without duplicating detailed frame telemetry.
    """

    # Composite Behavioral Identity
    dominant_goal: str | None = None
    dominant_skill: str | None = None
    dominant_target: str | None = None
    semantic_event_type: str | None = None

    # Compressed Milestone / Macro Transitions (Replacing bloated raw transition lists)
    macro_transitions: Tuple[MacroTransition, ...] = ()

    # Outcome & Consequence Representation (Replacing binary outcome_completed)
    outcome_status: OutcomeStatus = OutcomeStatus.UNKNOWN
    net_resource_deltas: Dict[str, float] = field(default_factory=dict)
    peak_emotions: Dict[str, float] = field(default_factory=dict)
    resource_summaries: Dict[str, StateSummary] = field(default_factory=dict)
    emotion_summaries: Dict[str, StateSummary] = field(default_factory=dict)

    # Environment & Spatial Context Reference
    max_hazard_exposure: float = 0.0
    max_reward_exposure: float = 0.0
    landmark_interactions: int = 0
    nearest_landmark_id: int | None = None
    environmental_exposure_flags: Tuple[str, ...] = ()

    # Retention Drivers & Descriptors (Score metrics like novelty/complexity removed to prevent duplication)
    primary_importance_drivers: Tuple[str, ...] = ()
    duration_ticks: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dominant_goal": self.dominant_goal,
            "dominant_skill": self.dominant_skill,
            "dominant_target": self.dominant_target,
            "semantic_event_type": self.semantic_event_type,
            "macro_transitions": [asdict(t) for t in self.macro_transitions],
            "outcome_status": (
                self.outcome_status.value
                if isinstance(self.outcome_status, Enum)
                else self.outcome_status
            ),
            "net_resource_deltas": dict(self.net_resource_deltas),
            "peak_emotions": dict(self.peak_emotions),
            "resource_summaries": {
                k: asdict(v) for k, v in self.resource_summaries.items()
            },
            "emotion_summaries": {
                k: asdict(v) for k, v in self.emotion_summaries.items()
            },
            "max_hazard_exposure": self.max_hazard_exposure,
            "max_reward_exposure": self.max_reward_exposure,
            "landmark_interactions": self.landmark_interactions,
            "nearest_landmark_id": self.nearest_landmark_id,
            "environmental_exposure_flags": list(self.environmental_exposure_flags),
            "primary_importance_drivers": list(self.primary_importance_drivers),
            "duration_ticks": self.duration_ticks,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EpisodeSignature":
        if not data:
            return cls()

        outcome_raw = data.get("outcome_status", OutcomeStatus.UNKNOWN.value)
        try:
            outcome_status = OutcomeStatus(outcome_raw)
        except ValueError:
            outcome_status = OutcomeStatus.UNKNOWN

        return cls(
            dominant_goal=data.get("dominant_goal"),
            dominant_skill=data.get("dominant_skill"),
            dominant_target=data.get("dominant_target"),
            semantic_event_type=data.get("semantic_event_type"),
            macro_transitions=tuple(
                MacroTransition(**t) for t in data.get("macro_transitions", [])
            ),
            outcome_status=outcome_status,
            net_resource_deltas=dict(data.get("net_resource_deltas", {})),
            peak_emotions=dict(data.get("peak_emotions", {})),
            resource_summaries={
                k: StateSummary(**v)
                for k, v in data.get("resource_summaries", {}).items()
            },
            emotion_summaries={
                k: StateSummary(**v)
                for k, v in data.get("emotion_summaries", {}).items()
            },
            max_hazard_exposure=data.get("max_hazard_exposure", 0.0),
            max_reward_exposure=data.get("max_reward_exposure", 0.0),
            landmark_interactions=data.get("landmark_interactions", 0),
            nearest_landmark_id=data.get("nearest_landmark_id"),
            environmental_exposure_flags=tuple(
                data.get("environmental_exposure_flags", ())
            ),
            primary_importance_drivers=tuple(
                data.get("primary_importance_drivers", ())
            ),
            duration_ticks=data.get("duration_ticks", 0),
        )


@dataclass(slots=True, frozen=True)
class EpisodeQuality:
    """
    Immutable, lightweight quality metrics for an EpisodicEvent.
    Serves as an operational signal for retention, ranking, and validation.
    """
    coherence: float = 1.0
    coverage: float = 1.0
    redundancy: float = 0.0
    novelty: float = 0.0
    recall_usefulness: float = 1.0
    overall_quality: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "coherence": self.coherence,
            "coverage": self.coverage,
            "redundancy": self.redundancy,
            "novelty": self.novelty,
            "recall_usefulness": self.recall_usefulness,
            "overall_quality": self.overall_quality,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EpisodeQuality":
        if not data:
            return cls()
        return cls(
            coherence=data.get("coherence", 1.0),
            coverage=data.get("coverage", 1.0),
            redundancy=data.get("redundancy", 0.0),
            novelty=data.get("novelty", 0.0),
            recall_usefulness=data.get("recall_usefulness", 1.0),
            overall_quality=data.get("overall_quality", 1.0),
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

    key_frames: List[SparseFrame] = field(default_factory=list)
    signature: EpisodeSignature = field(default_factory=EpisodeSignature)
    quality: EpisodeQuality | None = None
    notes: str | None = None

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
            "key_frames": [asdict(kf) for kf in self.key_frames],
            "signature": self.signature.to_dict(),
            "quality": self.quality.to_dict() if self.quality else None,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EpisodicEvent":
        if not data:
            return cls(
                start_tick=0, peak_tick=0, end_tick=0, event_type="",
                peak_significance=0.0, start_x=0.0, start_y=0.0,
                peak_x=0.0, peak_y=0.0, end_x=0.0, end_y=0.0
            )
        
        start_pos = data.get("start_position", {})
        peak_pos = data.get("peak_position", {})
        end_pos = data.get("end_position", {})

        kf_data = data.get("key_frames", [])
        key_frames = [SparseFrame.from_dict(kf) for kf in kf_data]

        sig_data = data.get("signature", {})
        signature = EpisodeSignature.from_dict(sig_data) if isinstance(sig_data, dict) else sig_data

        qual_data = data.get("quality")
        quality = EpisodeQuality.from_dict(qual_data) if qual_data else None

        return cls(
            start_tick=data.get("start_tick", 0),
            peak_tick=data.get("peak_tick", 0),
            end_tick=data.get("end_tick", 0),
            event_type=data.get("event_type", ""),
            peak_significance=data.get("peak_significance", 0.0),
            start_x=start_pos.get("x", 0.0),
            start_y=start_pos.get("y", 0.0),
            peak_x=peak_pos.get("x", 0.0),
            peak_y=peak_pos.get("y", 0.0),
            end_x=end_pos.get("x", 0.0),
            end_y=end_pos.get("y", 0.0),
            key_frames=key_frames,
            signature=signature,
            quality=quality,
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

@dataclass(slots=True, frozen=True)
class EpisodeMeta:
    """Lean metadata descriptor stored in the unified index for zero-load filtering."""
    id: int
    node_id: str
    event_type: str
    start_tick: int
    end_tick: int
    peak_tick: int
    peak_significance: float
    peak_x: float
    peak_y: float
    dominant_goal: str | None = None
    dominant_skill: str | None = None
    outcome_status: str = "unknown"
    overall_quality: float = 1.0
    nearest_landmark_id: int | None = None

    @classmethod
    def from_event(cls, event: "EpisodicEvent", episode_id: int | None = None) -> "EpisodeMeta":
        eid = episode_id if episode_id is not None else getattr(event, "id", event.start_tick)
        raw_outcome = event.signature.outcome_status
        outcome_val = raw_outcome.value if hasattr(raw_outcome, "value") else str(raw_outcome)

        return cls(
            id=eid,
            node_id=f"episode_{eid:06d}",
            event_type=event.event_type,
            start_tick=event.start_tick,
            end_tick=event.end_tick,
            peak_tick=event.peak_tick,
            peak_significance=event.peak_significance,
            peak_x=event.peak_x,
            peak_y=event.peak_y,
            dominant_goal=event.signature.dominant_goal,
            dominant_skill=event.signature.dominant_skill,
            outcome_status=outcome_val,
            overall_quality=event.quality.overall_quality if event.quality else 1.0,
            nearest_landmark_id=event.signature.nearest_landmark_id,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EpisodeMeta":
        return cls(
            id=data.get("id", 0),
            node_id=data.get("node_id", ""),
            event_type=data.get("event_type", ""),
            start_tick=data.get("start_tick", 0),
            end_tick=data.get("end_tick", 0),
            peak_tick=data.get("peak_tick", 0),
            peak_significance=data.get("peak_significance", 0.0),
            peak_x=data.get("peak_x", 0.0),
            peak_y=data.get("peak_y", 0.0),
            dominant_goal=data.get("dominant_goal"),
            dominant_skill=data.get("dominant_skill"),
            outcome_status=data.get("outcome_status", "unknown"),
            overall_quality=data.get("overall_quality", 1.0),
            nearest_landmark_id=data.get("nearest_landmark_id"),
        )

@dataclass(slots=True, frozen=True)
class LazyGroupSummary:
    """Lightweight cluster of contiguous episodes synthesized asynchronously or on-demand."""
    group_id: str
    episode_ids: Tuple[str, ...]
    start_tick: int
    end_tick: int
    dominant_goal: str | None = None
    dominant_skill: str | None = None
    nearest_landmark_id: int | None = None
    overall_quality: float = 1.0

    @property
    def duration_ticks(self) -> int:
        return self.end_tick - self.start_tick + 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_id": self.group_id,
            "episode_ids": list(self.episode_ids),
            "start_tick": self.start_tick,
            "end_tick": self.end_tick,
            "duration_ticks": self.duration_ticks,
            "dominant_goal": self.dominant_goal,
            "dominant_skill": self.dominant_skill,
            "nearest_landmark_id": self.nearest_landmark_id,
            "overall_quality": self.overall_quality,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LazyGroupSummary":
        return cls(
            group_id=data.get("group_id", ""),
            episode_ids=tuple(data.get("episode_ids", ())),
            start_tick=data.get("start_tick", 0),
            end_tick=data.get("end_tick", 0),
            dominant_goal=data.get("dominant_goal"),
            dominant_skill=data.get("dominant_skill"),
            nearest_landmark_id=data.get("nearest_landmark_id"),
            overall_quality=data.get("overall_quality", 1.0),
        )
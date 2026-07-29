from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


class MarkerType(str, Enum):
    """Categorical classification for timeline events and anchors."""

    START = "start"
    PEAK = "peak"
    END = "end"
    KEYFRAME = "keyframe"
    ANCHOR = "anchor"
    TRANSITION = "transition"


@dataclass(slots=True, frozen=True)
class TimelineMarker:
    """Represents a discrete temporal event on a 1D timeline axis."""

    tick: int
    marker_type: MarkerType
    label: str
    significance: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class StateTimeSeries:
    """Downsampled/normalized continuous metric curves for temporal graphing."""

    metric_name: str
    ticks: Tuple[int, ...]
    values: Tuple[float, ...]
    min_value: float = 0.0
    max_value: float = 1.0


@dataclass(slots=True, frozen=True)
class EpisodeTimeline:
    """Aggregated temporal structure for keyframes, phases, and state trends."""

    start_tick: int
    peak_tick: int
    end_tick: int
    duration_ticks: int
    markers: Tuple[TimelineMarker, ...] = ()
    state_series: Dict[str, StateTimeSeries] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class TransitionNode:
    """Primitive node capturing a discrete state in a behavioral flow graph."""

    tick: int
    state_category: str  # "goal", "skill", "target"
    state_value: Optional[str]


@dataclass(slots=True, frozen=True)
class TransitionEdge:
    """Directed connection representing a state change over time."""

    from_tick: int
    to_tick: int
    state_category: str
    from_state: Optional[str]
    to_state: Optional[str]


@dataclass(slots=True, frozen=True)
class BehaviorFlow:
    """Structured execution flow derived strictly from behavioral transitions."""

    dominant_goal: Optional[str]
    dominant_skill: Optional[str]
    dominant_target: Optional[str]
    outcome_completed: bool
    nodes: Tuple[TransitionNode, ...] = ()
    edges: Tuple[TransitionEdge, ...] = ()


@dataclass(slots=True, frozen=True)
class HierarchyNodeView:
    """Tree element mapping child/parent node relationships for visual graphs."""

    node_id: str
    level: str  # "episode", "group", "mission", "narrative", "custom"
    episode_id: Optional[str]
    parent_id: Optional[str]
    child_ids: Tuple[str, ...] = ()
    prev_id: Optional[str] = None
    next_id: Optional[str] = None
    relationship_types: Dict[str, str] = field(default_factory=dict)
    start_tick: int = 0
    end_tick: int = 0
    overall_quality: float = 1.0
    overall_importance: float = 0.0


@dataclass(slots=True, frozen=True)
class HierarchyView:
    """Aggregated view of structural hierarchy trees and relational links."""

    root_id: str
    nodes: Dict[str, HierarchyNodeView] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ReconstructionOverlay:
    """Visual overlay detailing anchor points, regions, and reconstruction confidence."""

    anchor_ticks: Tuple[int, ...] = ()
    compressed_regions: Tuple[Tuple[int, int], ...] = ()
    reconstructed_regions: Tuple[Tuple[int, int], ...] = ()
    confidence_ticks: Tuple[int, ...] = ()
    confidence_values: Tuple[float, ...] = ()


@dataclass(slots=True, frozen=True)
class EpisodeDebugView:
    """Diagnostic HUD metrics for quality evaluation, compression, and drivers."""

    quality_scores: Dict[str, float] = field(default_factory=dict)
    quality_reasons: Tuple[str, ...] = ()
    compression_ratio: float = 0.0
    information_density: float = 0.0
    original_keyframe_count: int = 0
    compressed_keyframe_count: int = 0
    primary_importance_drivers: Tuple[str, ...] = ()
    reconstruction: Optional[ReconstructionOverlay] = None


@dataclass(slots=True, frozen=True)
class PresentationPackage:
    """Root container holding all generated visual views for a selected memory item."""

    item_id: str
    timeline: Optional[EpisodeTimeline] = None
    flow: Optional[BehaviorFlow] = None
    hierarchy: Optional[HierarchyView] = None
    debug: Optional[EpisodeDebugView] = None

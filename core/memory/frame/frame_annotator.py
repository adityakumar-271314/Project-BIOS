from typing import Dict, Any, Optional
from ..schemas import TickSnapshot, EpisodeFrame
from .frame_rules import FrameRules
from .frame_changes import FrameChanges
from .frame_metrics import FrameMetrics


class FrameAnnotator:
    """
    Primary processing engine for frame generation.
    
    Owns rule evaluation, continuous state change tracking, and continuous 
    metric scoring to produce rich, extensible EpisodeFrame instances.
    """

    def __init__(self, config: Optional[Any] = None) -> None:
        self.config = config
        self.rules_engine = FrameRules()
        self.changes_engine = FrameChanges()
        self.metrics_engine = FrameMetrics()

    def _compute_deltas(self, prev: TickSnapshot, curr: TickSnapshot) -> Dict[str, float]:
        return {
            "energy_delta": curr.energy - prev.energy,
            "integrity_delta": curr.integrity - prev.integrity,
            "stress_delta": curr.stress - prev.stress,
            "fear_delta": curr.fear - prev.fear,
            "drive_delta": curr.drive - prev.drive,
        }

    def categorize_legacy_event(
        self, deltas: Dict[str, float], snapshot: TickSnapshot
    ) -> str:
        """Bridge fallback for legacy EpisodeBuilder downstream compatibility."""
        dmg_thresh = getattr(self.config, "episodic_damage_threshold", 0.05) if self.config else 0.05
        food_thresh = getattr(self.config, "episodic_food_recovery_threshold", 0.1) if self.config else 0.1
        fear_thresh = getattr(self.config, "episodic_danger_fear_threshold", 0.7) if self.config else 0.7
        drive_thresh = getattr(self.config, "episodic_starvation_drive_threshold", 0.7) if self.config else 0.7

        if deltas["integrity_delta"] < -dmg_thresh:
            return "damage_spike"
        if deltas["energy_delta"] > food_thresh:
            return "food_recovery"
        if snapshot.hazard_stim > 0.7:
            return "hazard_encounter"
        if snapshot.fear > fear_thresh:
            return "danger_state"
        if snapshot.drive > drive_thresh:
            return "starvation_state"
        return "high_significance"

    def annotate(
        self,
        prev_snapshot: Optional[TickSnapshot],
        curr_snapshot: TickSnapshot,
        stats: Dict[str, Any],
    ) -> EpisodeFrame:
        """
        Transforms raw consecutive snapshots into a fully annotated EpisodeFrame.
        """
        # Handle initial frame edge case where no previous snapshot exists
        if prev_snapshot is None:
            prev_snapshot = curr_snapshot

        deltas = self._compute_deltas(prev_snapshot, curr_snapshot)

        # 1. Run Domain Workers
        event_tags = self.rules_engine.evaluate(
            prev=prev_snapshot, curr=curr_snapshot, config=self.config
        )
        
        change_mask, transition_flags = self.changes_engine.compute(
            prev=prev_snapshot, curr=curr_snapshot
        )

        metrics = self.metrics_engine.compute(
            prev=prev_snapshot,
            curr=curr_snapshot,
            deltas=deltas,
            event_tags=event_tags,
            transition_flags=transition_flags,
            stats=stats,
            config=self.config,
        )

        # 2. Derive Legacy Compatibility Fields
        legacy_event_type = self.categorize_legacy_event(deltas, curr_snapshot)
        legacy_significance = metrics["importance"]

        # 3. Construct and Return Rich Frame
        return EpisodeFrame(
            snapshot=curr_snapshot,
            # Legacy Bridge Fields
            significance=legacy_significance,
            event_type=legacy_event_type,
            # Deltas
            energy_delta=deltas["energy_delta"],
            integrity_delta=deltas["integrity_delta"],
            stress_delta=deltas["stress_delta"],
            fear_delta=deltas["fear_delta"],
            drive_delta=deltas["drive_delta"],
            # Part A Rich Metrics
            importance=metrics["importance"],
            prediction_error=metrics["prediction_error"],
            attention_score=metrics["attention_score"],
            novelty=metrics["novelty"],
            # Structural Signals
            event_tags=event_tags,
            transition_flags=transition_flags,
            change_mask=change_mask,
        )
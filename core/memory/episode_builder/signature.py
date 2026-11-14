from typing import List
from collections import Counter
from ..schemas import (
    EpisodeFrame,
    EpisodeSignature,
    StateSummary,
    MacroTransition,
    OutcomeStatus,
)
from .config import EpisodeBuilderConfig


class SignatureBuilder:
    """Constructs high-level behavioral identities, macro-transitions, resource summaries, and qualitative outcomes."""

    def __init__(self, config: EpisodeBuilderConfig):
        self.config = config

    def build(self, window: List[EpisodeFrame]) -> EpisodeSignature:
        """Synthesizes an EpisodeSignature summary from a validated window of episode frames."""
        if not window:
            return EpisodeSignature()

        behavior_tuples = [
            (f.snapshot.goal_name, f.snapshot.active_skill, f.snapshot.target_type)
            for f in window
        ]
        dom_goal, dom_skill, dom_target = (
            Counter(behavior_tuples).most_common(1)[0][0]
            if behavior_tuples
            else (None, None, None)
        )

        peak_frame = max(window, key=lambda f: f.importance, default=window[0])
        semantic_event_type = (
            peak_frame.event_type if peak_frame else "high_significance"
        )

        macro_trans: List[MacroTransition] = []
        min_dwell_ticks = max(5, int(len(window) * 0.1))

        def _extract_milestones(field_name: str, transition_label: str):
            current_val = getattr(window[0].snapshot, field_name)
            run_start_tick = window[0].snapshot.tick
            last_val = current_val
            for f in window[1:]:
                val = getattr(f.snapshot, field_name)
                if val != last_val:
                    if (
                        f.snapshot.tick - run_start_tick >= min_dwell_ticks
                        and last_val is not None
                    ):
                        macro_trans.append(
                            MacroTransition(
                                from_state=current_val,
                                to_state=last_val,
                                transition_type=transition_label,
                            )
                        )
                        current_val = last_val
                    last_val = val
                    run_start_tick = f.snapshot.tick

        _extract_milestones("goal_name", "goal")
        _extract_milestones("active_skill", "skill")
        _extract_milestones("target_type", "target")

        last_snap = window[-1].snapshot
        if last_snap.action_state == "complete":
            outcome_status = OutcomeStatus.COMPLETED
        elif last_snap.action_state == "aborted":
            outcome_status = OutcomeStatus.ABORTED
        elif last_snap.action_state == "timeout":
            outcome_status = OutcomeStatus.TIMEOUT
        elif (
            any(f.snapshot.integrity <= 0.0 for f in window)
            or last_snap.integrity < 0.1
        ):
            outcome_status = OutcomeStatus.FAILED
        elif any(
            "damage_taken" in f.event_tags or "entered_hazard" in f.event_tags
            for f in window
        ):
            outcome_status = OutcomeStatus.INTERRUPTED
        else:
            outcome_status = OutcomeStatus.COMPLETED

        net_resource_deltas = {
            "energy": window[-1].snapshot.energy - window[0].snapshot.energy,
            "integrity": window[-1].snapshot.integrity - window[0].snapshot.integrity,
            "drive": window[-1].snapshot.drive - window[0].snapshot.drive,
        }
        peak_emotions = {
            "max_fear": max((f.snapshot.fear for f in window), default=0.0),
            "max_stress": max((f.snapshot.stress for f in window), default=0.0),
        }

        def _summarize(vals: List[float]) -> StateSummary:
            return StateSummary(
                initial=vals[0], final=vals[-1], min_val=min(vals), max_val=max(vals)
            )

        resource_summaries = {
            "energy": _summarize([f.snapshot.energy for f in window]),
            "integrity": _summarize([f.snapshot.integrity for f in window]),
        }
        emotion_summaries = {
            "fear": _summarize([f.snapshot.fear for f in window]),
            "stress": _summarize([f.snapshot.stress for f in window]),
            "drive": _summarize([f.snapshot.drive for f in window]),
        }

        max_hazard = max((f.snapshot.hazard_stim for f in window), default=0.0)
        max_reward = max((f.snapshot.food_stim for f in window), default=0.0)
        landmarks = max((f.snapshot.visible_landmarks for f in window), default=0)

        target_ids = [
            f.snapshot.target_id for f in window if f.snapshot.target_id is not None
        ]
        nearest_landmark_id = (
            Counter(target_ids).most_common(1)[0][0] if target_ids else None
        )
        env_flags = set()
        if max_hazard > 0.5:
            env_flags.add("high_hazard_zone")
        if max_reward > 0.5:
            env_flags.add("reward_patch")
        if landmarks > 0:
            env_flags.add("landmark_visible")

        drivers = set()
        if any(f.novelty > 0.4 for f in window):
            drivers.add("high_novelty")
        if macro_trans:
            drivers.add("behavioral_shift")
        if max_hazard > 0.5:
            drivers.add("hazard_exposure")
        if max_reward > 0.5:
            drivers.add("reward_acquisition")
        if abs(resource_summaries["integrity"].net_change) > 0.15:
            drivers.add("integrity_change")

        duration = window[-1].snapshot.tick - window[0].snapshot.tick + 1
        return EpisodeSignature(
            dominant_goal=dom_goal,
            dominant_skill=dom_skill,
            dominant_target=dom_target,
            semantic_event_type=semantic_event_type,
            macro_transitions=tuple(macro_trans),
            outcome_status=outcome_status,
            net_resource_deltas=net_resource_deltas,
            peak_emotions=peak_emotions,
            resource_summaries=resource_summaries,
            emotion_summaries=emotion_summaries,
            max_hazard_exposure=max_hazard,
            max_reward_exposure=max_reward,
            landmark_interactions=landmarks,
            nearest_landmark_id=nearest_landmark_id,
            environmental_exposure_flags=tuple(sorted(env_flags)),
            primary_importance_drivers=tuple(sorted(drivers)),
            duration_ticks=duration,
        )

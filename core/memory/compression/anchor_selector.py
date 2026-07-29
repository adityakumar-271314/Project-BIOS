from typing import List, Set
from ..schemas import EpisodicEvent, SparseFrame


class AnchorSelector:
    """
    Selects candidate keyframes (anchors) that deserve to survive compression.
    Identifies structurally and behaviorally critical frames from an EpisodicEvent's
    existing key_frames without modifying signatures, pruning, or reordering.
    """

    def select_candidate_anchors(self, event: EpisodicEvent) -> List[SparseFrame]:
        if not event.key_frames:
            return []

        # Map frames by tick for quick lookup and deterministic sorting
        frame_map = {kf.tick: kf for kf in event.key_frames}
        sorted_ticks = sorted(frame_map.keys())

        anchors_to_keep: Set[int] = set()

        # 1. Always preserve start, peak, and end ticks
        anchors_to_keep.add(event.start_tick)
        anchors_to_keep.add(event.peak_tick)
        anchors_to_keep.add(event.end_tick)

        # 2. Preserve signature transition ticks (behavioral state shifts)
        sig = event.signature
        if sig:
            for trans in sig.goal_transitions:
                anchors_to_keep.add(trans.tick)
            for trans in sig.skill_transitions:
                anchors_to_keep.add(trans.tick)
            for trans in sig.target_transitions:
                anchors_to_keep.add(trans.tick)

        # 3. Preserve large behavioral, environmental, and high density regions across existing keyframes
        for i, frame in enumerate(event.key_frames):
            # High significance / information density
            if frame.significance >= 0.6:
                anchors_to_keep.add(frame.tick)

            # Environmental presence (hazards or food)
            if frame.visible_food > 0 or frame.visible_hazards > 0:
                anchors_to_keep.add(frame.tick)

            # Neighboring state shifts (action state or skill changes between consecutive keyframes)
            if i > 0:
                prev = event.key_frames[i - 1]
                if (
                    frame.active_skill != prev.active_skill
                    or frame.action_state != prev.action_state
                    or frame.target_type != prev.target_type
                ):
                    anchors_to_keep.add(prev.tick)
                    anchors_to_keep.add(frame.tick)

        # Collect and return sorted candidate anchors that match our selected ticks
        candidate_anchors = [frame_map[t] for t in sorted_ticks if t in frame_map]

        # If boundary ticks (start/peak/end) were missing from key_frames, build fallback SparseFrames for them
        existing_ticks = {f.tick for f in candidate_anchors}
        for boundary_tick in (event.start_tick, event.peak_tick, event.end_tick):
            if boundary_tick not in existing_ticks:
                if boundary_tick == event.peak_tick and event.peak_snapshot:
                    snap = event.peak_snapshot
                    candidate_anchors.append(
                        SparseFrame(
                            tick=snap.tick,
                            pos_x=snap.pos_x,
                            pos_y=snap.pos_y,
                            vel_x=snap.vel_x,
                            vel_y=snap.vel_y,
                            heading=snap.heading,
                            energy=snap.energy,
                            integrity=snap.integrity,
                            stress=snap.stress,
                            fear=snap.fear,
                            drive=snap.drive,
                            significance=event.peak_significance,
                            active_skill=snap.active_skill,
                            action_state=snap.action_state,
                            target_type=snap.target_type,
                            visible_food=snap.visible_food,
                            visible_hazards=snap.visible_hazards,
                            notes=snap.notes,
                        )
                    )

        candidate_anchors.sort(key=lambda f: f.tick)
        return candidate_anchors

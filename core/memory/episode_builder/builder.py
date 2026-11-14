from typing import List, Optional
from ..boundary.boundary import BoundaryInterval
from ..boundary.boundary_detector import BoundaryDetector
from ..schemas import EpisodicEvent, EpisodeFrame
from .config import EpisodeBuilderConfig
from .windowing import WindowExtractor
from .signature import SignatureBuilder
from .keyframes import KeyframeExtractor


class EpisodeBuilder:
    """Main orchestrator coordinating windowing, keyframe extraction, and signature building to produce EpisodicEvents."""

    def __init__(
        self,
        config: Optional[EpisodeBuilderConfig] = None,
        boundary_detector: Optional[BoundaryDetector] = None,
    ):
        """Initializes the orchestrator with configuration overrides and modular service components."""
        self.config = config or EpisodeBuilderConfig()
        self.boundary_detector = boundary_detector or BoundaryDetector()

        # Instantiate modular service classes
        self.window_extractor = WindowExtractor(self.config)
        self.signature_builder = SignatureBuilder(self.config)
        self.keyframe_extractor = KeyframeExtractor(self.config)

    def build(
        self,
        frames: List[EpisodeFrame],
        boundaries: Optional[List[BoundaryInterval]] = None,
    ) -> List[EpisodicEvent]:
        """Processes frame sequences and boundary intervals into a structured list of EpisodicEvent instances."""
        if not frames:
            return []
        if boundaries is None:
            boundaries = self.boundary_detector.detect_boundaries(frames)
        if not boundaries:
            return []

        frame_map = {f.snapshot.tick: f for f in frames}
        sorted_ticks = sorted(frame_map.keys())
        min_available_tick = sorted_ticks[0]
        episodes = []

        for idx, interval in enumerate(boundaries):
            prev_end_tick = (
                boundaries[idx - 1].end_tick if idx > 0 else min_available_tick
            )

            window_frames = self.window_extractor.extract_asymmetric_window(
                interval=interval,
                sorted_ticks=sorted_ticks,
                frame_map=frame_map,
                prev_end_tick=prev_end_tick,
                min_available_tick=min_available_tick,
            )
            if not window_frames:
                continue

            peak_frame = max(window_frames, key=lambda f: f.importance)
            first_snap = window_frames[0].snapshot
            last_snap = window_frames[-1].snapshot

            key_frames = self.keyframe_extractor.extract(window_frames)
            signature = self.signature_builder.build(window_frames)

            start_reasons_str = ",".join(interval.start_reasons)
            end_reasons_str = ",".join(interval.end_reasons)
            notes_str = (
                f"Start: [{start_reasons_str}] (Asymmetric) | End: [{end_reasons_str}]"
            )
            if peak_frame.snapshot.notes:
                notes_str += f" | {peak_frame.snapshot.notes}"

            episode = EpisodicEvent(
                start_tick=first_snap.tick,
                peak_tick=peak_frame.snapshot.tick,
                end_tick=last_snap.tick,
                event_type=peak_frame.event_type,
                peak_significance=peak_frame.importance,
                start_x=first_snap.pos_x,
                start_y=first_snap.pos_y,
                peak_x=peak_frame.snapshot.pos_x,
                peak_y=peak_frame.snapshot.pos_y,
                end_x=last_snap.pos_x,
                end_y=last_snap.pos_y,
                key_frames=key_frames,
                signature=signature,
                notes=notes_str,
            )
            episodes.append(episode)

        return episodes

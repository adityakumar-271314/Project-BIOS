from .episode_builder import EpisodeBuilder
from .boundary.boundary_detector import BoundaryDetector


class EpisodePipeline:
    def __init__(self, episodic_memory, temporal_buffer, boundary_detector=None):
        self.boundary_detector = boundary_detector or BoundaryDetector()
        self.builder = EpisodeBuilder(boundary_detector=self.boundary_detector)
        self.temporal_buffer = temporal_buffer

    def process_candidate(self, candidate_tick: int):
        print(f"[PIPELINE] Retrospective boundary detection & build for tick {candidate_tick}")
        # Pull annotated frames from buffer
        frames = self.temporal_buffer.get_frame_context(
            center_tick=candidate_tick,
            before_ticks=300,
            after_ticks=180,
        )
        if not frames:
            return []

        # Run boundary detection pipeline to extract clean intervals
        boundaries = self.boundary_detector.detect_boundaries(frames)

        # Build events from detected boundaries
        return self.builder.build(frames, boundaries=boundaries)
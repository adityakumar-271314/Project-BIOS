from .episode_builder import EpisodeBuilder

class EpisodePipeline:
    def __init__(self, episodic_memory, temporal_buffer):
        self.builder = EpisodeBuilder()
        self.temporal_buffer = temporal_buffer

    def process_candidate(self, candidate_tick: int):
        print(f"[PIPELINE] Retrospective processing for target tick {candidate_tick}")
        # Zero conversion overhead: Pull pre-computed frames directly
        frames = self.temporal_buffer.get_frame_context(
            center_tick=candidate_tick,
            before_ticks=300,
            after_ticks=180,
        )
        return self.builder.build(frames)
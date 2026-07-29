from typing import List, Optional
from ..schemas import EpisodicEvent
from .anchor_selector import AnchorSelector
from .redundancy_pruner import RedundancyPruner
from .compression_analyzer import CompressionAnalyzer


class EpisodeCompressor:
    """
    Main entry point for compressing EpisodicEvent instances.

    Coordinates candidate anchor selection, redundancy pruning, and metadata generation.
    Replaces key_frames with compressed anchors and attaches CompressionMetadata directly.
    """

    def __init__(
        self,
        anchor_selector: Optional[AnchorSelector] = None,
        redundancy_pruner: Optional[RedundancyPruner] = None,
        compression_analyzer: Optional[CompressionAnalyzer] = None,
    ):
        self.anchor_selector = anchor_selector or AnchorSelector()
        self.redundancy_pruner = redundancy_pruner or RedundancyPruner()
        self.compression_analyzer = compression_analyzer or CompressionAnalyzer()

    def compress_episode(self, event: EpisodicEvent) -> EpisodicEvent:
        """
        Compresses a single EpisodicEvent in-place / directly and returns it.
        """
        original_frames = list(event.key_frames)

        # 1. Run AnchorSelector to find candidates
        candidate_anchors = self.anchor_selector.select_candidate_anchors(event)

        # 2. Run RedundancyPruner to eliminate unnecessary anchors
        compressed_anchors = self.redundancy_pruner.prune_anchors(
            candidate_anchors, event
        )

        # 3. Generate CompressionMetadata via CompressionAnalyzer
        metadata = self.compression_analyzer.analyze(
            event=event,
            original_frames=original_frames,
            compressed_frames=compressed_anchors,
        )

        # 4. Replace event key_frames and attach metadata
        event.key_frames = compressed_anchors
        event.compression = metadata

        return event

    def compress_batch(self, events: List[EpisodicEvent]) -> List[EpisodicEvent]:
        """
        Compresses a batch of EpisodicEvent instances.
        """
        return [self.compress_episode(event) for event in events]

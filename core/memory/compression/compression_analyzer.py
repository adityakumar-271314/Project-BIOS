from typing import List
from ..schemas import CompressionMetadata, EpisodicEvent, SparseFrame


class CompressionAnalyzer:
    """
    Measures the results of keyframe compression on an EpisodicEvent.

    Responsibility: Measure what was kept (ratios, densities, counts).
    Does NOT calculate MSE, interpolation error, or reconstruction confidence,
    as the compressed representation becomes the self-contained source of truth.
    """

    def analyze(
        self,
        event: EpisodicEvent,
        original_frames: List[SparseFrame],
        compressed_frames: List[SparseFrame],
        strategy: str = "anchor_pruning",
    ) -> CompressionMetadata:
        orig_count = len(original_frames)
        comp_count = len(compressed_frames)

        # Handle edge cases where original frame count is zero
        if orig_count == 0:
            return CompressionMetadata(
                compression_ratio=1.0,
                original_keyframe_count=0,
                compressed_keyframe_count=0,
                information_density=1.0,
                compression_strategy=strategy,
            )

        # Ratio of retained frames to original keyframes
        compression_ratio = round(comp_count / orig_count, 4)

        # Measure retained information density (weighted sum of preserved significance)
        orig_significance_sum = sum(f.significance for f in original_frames)
        comp_significance_sum = sum(f.significance for f in compressed_frames)

        if orig_significance_sum > 0:
            info_density = round(comp_significance_sum / orig_significance_sum, 4)
        else:
            info_density = round(comp_count / orig_count, 4)

        return CompressionMetadata(
            compression_ratio=compression_ratio,
            original_keyframe_count=orig_count,
            compressed_keyframe_count=comp_count,
            information_density=info_density,
            compression_strategy=strategy,
        )

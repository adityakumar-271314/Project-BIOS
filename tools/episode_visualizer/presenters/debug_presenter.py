# FILE: tools/episode_visualizer/presenters/debug_presenter.py
from typing import List, Optional

from core.memory.schemas import EpisodicEvent, ReconstructedTick
from tools.episode_visualizer.presenters.schemas import (
    EpisodeDebugView,
    ReconstructionOverlay,
)


class DebugPresenter:
    """
    Pure presenter component that computes and formats diagnostic HUD metrics,
    compression statistics, and quality scores for visualization.
    """

    @staticmethod
    def present(
        event: EpisodicEvent,
        reconstructed_ticks: Optional[List[ReconstructedTick]] = None,
    ) -> EpisodeDebugView:
        duration_ticks = max(1, event.end_tick - event.start_tick)
        keyframe_count = len(event.key_frames)

        # 1. Compute compression & density statistics
        compression_ratio = keyframe_count / float(duration_ticks)
        information_density = (
            event.peak_significance / float(keyframe_count)
            if keyframe_count > 0
            else 0.0
        )

        # 2. Map quality scores and evaluation drivers
        overall_quality = getattr(
            event, "overall_quality", getattr(event, "quality_score", 1.0)
        )
        peak_sig = getattr(event, "peak_significance", 0.0)

        quality_scores = {
            "overall_quality": float(overall_quality),
            "peak_significance": float(peak_sig),
            "coherence": float(getattr(event, "coherence_score", 1.0)),
        }

        quality_reasons = tuple(getattr(event, "quality_reasons", ()))
        importance_drivers = tuple(getattr(event.signature, "primary_drivers", ()))

        # 3. Build reconstruction overlay metrics if present
        reconstruction_overlay: Optional[ReconstructionOverlay] = None
        if reconstructed_ticks:
            anchor_ticks = tuple(rt.tick for rt in reconstructed_ticks if rt.anchor)
            confidence_ticks = tuple(rt.tick for rt in reconstructed_ticks)
            confidence_values = tuple(
                float(rt.confidence) for rt in reconstructed_ticks
            )

            # Extract interpolated/reconstructed continuous tick ranges
            reconstructed_regions = DebugPresenter._extract_contiguous_regions(
                [rt.tick for rt in reconstructed_ticks if not rt.anchor]
            )

            reconstruction_overlay = ReconstructionOverlay(
                anchor_ticks=anchor_ticks,
                reconstructed_regions=reconstructed_regions,
                confidence_ticks=confidence_ticks,
                confidence_values=confidence_values,
            )

        return EpisodeDebugView(
            quality_scores=quality_scores,
            quality_reasons=quality_reasons,
            compression_ratio=compression_ratio,
            information_density=information_density,
            original_keyframe_count=duration_ticks,
            compressed_keyframe_count=keyframe_count,
            primary_importance_drivers=importance_drivers,
            reconstruction=reconstruction_overlay,
        )

    @staticmethod
    def _extract_contiguous_regions(
        ticks: List[int],
    ) -> tuple[tuple[int, int], ...]:
        """Groups contiguous tick numbers into start-end boundary tuple pairs."""
        if not ticks:
            return ()

        sorted_ticks = sorted(set(ticks))
        regions = []
        start = sorted_ticks[0]
        prev = start

        for tick in sorted_ticks[1:]:
            if tick == prev + 1:
                prev = tick
            else:
                regions.append((start, prev))
                start = tick
                prev = tick
        regions.append((start, prev))

        return tuple(regions)

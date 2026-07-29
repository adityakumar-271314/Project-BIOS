# FILE: tools/episode_visualizer/presenters/timeline_presenter.py
from typing import Dict, List, Optional, Tuple

from core.memory.schemas import EpisodicEvent, ReconstructedTick, SparseFrame
from tools.episode_visualizer.presenters.schemas import (
    EpisodeTimeline,
    MarkerType,
    StateTimeSeries,
    TimelineMarker,
)


class TimelinePresenter:
    """
    Pure presenter component that maps EpisodicEvent data into an EpisodeTimeline.
    Handles marker placement, keyframe alignment, and state downsampling/formatting.
    """

    @staticmethod
    def present(
        event: EpisodicEvent,
        reconstructed_ticks: Optional[List[ReconstructedTick]] = None,
    ) -> EpisodeTimeline:
        duration_ticks = event.end_tick - event.start_tick

        markers = TimelinePresenter._extract_markers(event, reconstructed_ticks)
        state_series = TimelinePresenter._build_state_series(event, reconstructed_ticks)

        return EpisodeTimeline(
            start_tick=event.start_tick,
            peak_tick=event.peak_tick,
            end_tick=event.end_tick,
            duration_ticks=duration_ticks,
            markers=tuple(markers),
            state_series=state_series,
        )

    @staticmethod
    def _extract_markers(
        event: EpisodicEvent,
        reconstructed_ticks: Optional[List[ReconstructedTick]] = None,
    ) -> List[TimelineMarker]:
        markers: List[TimelineMarker] = []

        # Start, Peak, End Phase Markers
        markers.append(
            TimelineMarker(
                tick=event.start_tick,
                marker_type=MarkerType.START,
                label="Episode Start",
            )
        )
        markers.append(
            TimelineMarker(
                tick=event.peak_tick,
                marker_type=MarkerType.PEAK,
                label="Peak Significance",
                significance=event.peak_significance,
            )
        )
        markers.append(
            TimelineMarker(
                tick=event.end_tick,
                marker_type=MarkerType.END,
                label="Episode End",
            )
        )

        # Keyframe Markers from SparseFrames / Signature
        existing_ticks = {m.tick for m in markers}
        keyframe_ticks_from_sig = set(event.signature.keyframe_ticks)

        for kf in event.key_frames:
            if kf.tick not in existing_ticks:
                markers.append(
                    TimelineMarker(
                        tick=kf.tick,
                        marker_type=MarkerType.KEYFRAME,
                        label="Keyframe",
                        significance=kf.significance,
                    )
                )
                existing_ticks.add(kf.tick)

        for tick in keyframe_ticks_from_sig:
            if tick not in existing_ticks:
                markers.append(
                    TimelineMarker(
                        tick=tick,
                        marker_type=MarkerType.KEYFRAME,
                        label="Keyframe Reference",
                    )
                )
                existing_ticks.add(tick)

        # Anchor Markers from Reconstruction Data if provided
        if reconstructed_ticks:
            for rt in reconstructed_ticks:
                if rt.anchor and rt.tick not in existing_ticks:
                    markers.append(
                        TimelineMarker(
                            tick=rt.tick,
                            marker_type=MarkerType.ANCHOR,
                            label="Reconstruction Anchor",
                            significance=rt.confidence,
                        )
                    )
                    existing_ticks.add(rt.tick)

        markers.sort(key=lambda m: m.tick)
        return markers

    @staticmethod
    def _build_state_series(
        event: EpisodicEvent,
        reconstructed_ticks: Optional[List[ReconstructedTick]] = None,
    ) -> Dict[str, StateTimeSeries]:
        series_map: Dict[str, StateTimeSeries] = {}

        # 1. Prefer full-resolution timeline from reconstructed ticks if available
        if reconstructed_ticks:
            ticks = tuple(rt.tick for rt in reconstructed_ticks)
            metrics = ["energy", "integrity", "stress", "fear", "drive"]

            for metric in metrics:
                vals = tuple(
                    float(getattr(rt, metric, 0.0)) for rt in reconstructed_ticks
                )
                if vals:
                    series_map[metric] = StateTimeSeries(
                        metric_name=metric,
                        ticks=ticks,
                        values=vals,
                        min_value=min(vals),
                        max_value=max(vals),
                    )
            return series_map

        # 2. Fallback to sparse keyframes when no reconstructed ticks exist
        if event.key_frames:
            sorted_kfs = sorted(event.key_frames, key=lambda kf: kf.tick)
            ticks = tuple(kf.tick for kf in sorted_kfs)
            metrics = ["energy", "integrity", "stress", "fear", "drive"]

            for metric in metrics:
                vals = tuple(float(getattr(kf, metric, 0.0)) for kf in sorted_kfs)
                if vals:
                    series_map[metric] = StateTimeSeries(
                        metric_name=metric,
                        ticks=ticks,
                        values=vals,
                        min_value=min(vals),
                        max_value=max(vals),
                    )

        return series_map

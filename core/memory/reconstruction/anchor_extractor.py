from ..schemas import EpisodicEvent, SparseFrame
from typing import List


def extract_anchors(event: EpisodicEvent) -> List[SparseFrame]:
    """Extracts sorted unique anchor frames directly from event keyframes."""
    anchors = list(event.key_frames)

    # Fallback guarantee: ensure peak tick is present in anchors if missing
    if event.peak_frame and not any(k.tick == event.peak_frame.tick for k in anchors):
        anchors.append(event.peak_frame)

    anchors.sort(key=lambda x: x.tick)
    return anchors

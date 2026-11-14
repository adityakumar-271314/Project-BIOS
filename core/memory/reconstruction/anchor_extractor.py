from ..schemas import EpisodicEvent, SparseFrame
from typing import List


def extract_anchors(event: EpisodicEvent) -> List[SparseFrame]:
    """Extracts sorted unique anchor frames directly from event keyframes."""
    anchors = list(event.key_frames)

    peak_f = getattr(event, "peak_frame", None)
    if peak_f and not any(k.tick == peak_f.tick for k in anchors):
        anchors.append(peak_f)

    anchors.sort(key=lambda x: x.tick)
    return anchors

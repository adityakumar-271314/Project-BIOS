from ..schemas import EpisodicEvent, SparseFrame


def extract_anchors(event: EpisodicEvent):
    anchors = []
    peak = event.peak_snapshot
    anchors.extend(event.key_frames)
    # ensure peak included
    if not any(k.tick == peak.tick for k in anchors):
        anchors.append(peak)
    anchors.sort(key=lambda x: x.tick)
    return anchors

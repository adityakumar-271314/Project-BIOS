from .anchor_extractor import extract_anchors
from .interpolator import interpolate_segment


class EpisodeReconstructor:

    def reconstruct(self, event):
        anchors = extract_anchors(event)
        if len(anchors) < 2:
            return []
        reconstructed = []
        for i in range(len(anchors) - 1):
            seg = interpolate_segment(anchors[i], anchors[i + 1])
            if i > 0:
                seg = seg[1:]
            reconstructed.extend(seg)
        return reconstructed

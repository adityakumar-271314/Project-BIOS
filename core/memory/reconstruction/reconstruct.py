from .anchor_extractor import extract_anchors
from .interpolator import interpolate_segment
from typing import List
from .validator import EpisodeReconstructionValidator
from ..schemas import EpisodeFrame


class EpisodeReconstructor:
    def __init__(self, validator: EpisodeReconstructionValidator = None):
        self.validator = validator or EpisodeReconstructionValidator()

    def reconstruct(self, event, original_frames: List[EpisodeFrame] = None):
        anchors = extract_anchors(event)
        if len(anchors) < 2:
            return []

        reconstructed = []
        for i in range(len(anchors) - 1):
            seg = interpolate_segment(anchors[i], anchors[i + 1])
            if i > 0:
                seg = seg[1:]
            reconstructed.extend(seg)

        # Run error guardrail validation if raw frames are available
        if original_frames:
            validation_report = self.validator.validate_segment(
                original_frames, reconstructed
            )
            if not validation_report["valid"]:
                # Guardrail tripped: handle fallback or log warning on reconstruction drift
                pass

        return reconstructed

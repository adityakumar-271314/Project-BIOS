from typing import List, Dict, Any
from ..schemas import EpisodeFrame, ReconstructedTick


class EpisodeReconstructionValidator:
    """
    Measures reconstruction error between original raw frames and
    linearly interpolated reconstructed ticks.
    """

    def __init__(
        self,
        max_position_drift: float = 0.5,  # Max allowed distance drift (units)
        max_vital_drift: float = 0.08,  # Max allowed energy/integrity drift
        max_heading_drift_rad: float = 0.4,  # Max allowed heading angle deviation
    ):
        self.max_position_drift = max_position_drift
        self.max_vital_drift = max_vital_drift
        self.max_heading_drift_rad = max_heading_drift_rad

    def validate_segment(
        self,
        original_frames: List[EpisodeFrame],
        reconstructed_ticks: List[ReconstructedTick],
    ) -> Dict[str, Any]:
        """
        Computes error metrics across spatial, vital, and kinematic axes.
        """
        if not original_frames or not reconstructed_ticks:
            return {"valid": True, "max_pos_error": 0.0, "max_vital_error": 0.0}

        # Map reconstructed ticks by tick for O(1) lookup
        recon_map = {r.tick: r for r in reconstructed_ticks}

        pos_errors = []
        vital_errors = []
        heading_errors = []

        for frame in original_frames:
            t = frame.snapshot.tick
            if t not in recon_map:
                continue

            orig = frame.snapshot
            recon = recon_map[t]

            # 1. Spatial Euclidean distance error
            pos_err = (
                (orig.pos_x - recon.pos_x) ** 2 + (orig.pos_y - recon.pos_y) ** 2
            ) ** 0.5
            pos_errors.append(pos_err)

            # 2. Vital deviation error (energy & integrity average)
            vital_err = (
                abs(orig.energy - recon.energy) + abs(orig.integrity - recon.integrity)
            ) / 2.0
            vital_errors.append(vital_err)

            # 3. Heading angular deviation
            heading_diff = abs(
                (orig.heading - recon.heading + 3.14159) % (6.28318) - 3.14159
            )
            heading_errors.append(heading_diff)

        max_pos_error = max(pos_errors) if pos_errors else 0.0
        max_vital_error = max(vital_errors) if vital_errors else 0.0
        max_heading_error = max(heading_errors) if heading_errors else 0.0

        is_valid = (
            max_pos_error <= self.max_position_drift
            and max_vital_error <= self.max_vital_drift
            and max_heading_error <= self.max_heading_drift_rad
        )

        return {
            "valid": is_valid,
            "max_position_error": max_pos_error,
            "max_vital_error": max_vital_error,
            "max_heading_error": max_heading_error,
        }

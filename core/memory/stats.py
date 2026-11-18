"""Online statistics used to judge what counts as 'normal' experience (Welford)."""
from __future__ import annotations
import math
from typing import Dict


class RunningStats:
    def __init__(self):
        self.n = 0
        self.mean = 0.0
        self.M2 = 0.0

    def update(self, value: float) -> None:
        self.n += 1
        delta = value - self.mean
        self.mean += delta / self.n
        self.M2 += delta * (value - self.mean)

    @property
    def variance(self) -> float:
        return self.M2 / (self.n - 1) if self.n > 1 else 0.0

    @property
    def std(self) -> float:
        return math.sqrt(self.variance)


STAT_KEYS = ("energy_delta", "integrity_delta", "stress_delta", "fear_delta", "drive_delta")


def new_stats_bank() -> Dict[str, RunningStats]:
    return {k: RunningStats() for k in STAT_KEYS}

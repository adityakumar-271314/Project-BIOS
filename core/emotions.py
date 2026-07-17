"""
EmotionHormoneEngine — Affective and Motivational System.

Translates physiological states (energy, integrity) and environmental
stimuli (hazards, walls) into internal drives:
- drive (hunger)
- fear (threat response)
- stress (general arousal/damage)

These signals modulate both goal selection and motor behavior.
"""

from infra.constants import MAX_ENERGY, MAX_INTEGRITY


class EmotionHormoneEngine:
    def __init__(self, config):
        self.cfg = config
        self.stress = 0.0
        self.fear = 0.0
        self.drive = 0.0

    def update(self, bst, sensor_data):
        #  DRIVE: Normalized hunger
        self.drive = (MAX_ENERGY - bst.energy) / 100.0
        hazard_stim = sensor_data.hazard_stim
        if hazard_stim > self.cfg.hazard_trigger_threshold:
            self.fear = min(1.0, self.fear + self.cfg.fear_increase_rate)
        else:
            self.fear = max(0.0, self.fear - self.cfg.fear_decay_rate)

        #  STRESS: Walls + Pain
        integrity_stress = (MAX_INTEGRITY - bst.integrity) / 100.0
        rc = sensor_data.ray_c
        wall_pressure = (1 - rc) if rc < self.cfg.wall_stress_threshold else 0.0

        target_stress = max(integrity_stress, wall_pressure)
        self.stress += (target_stress - self.stress) * self.cfg.stress_lerp_rate

from ..schemas import ReconstructedTick


def lerp(a, b, alpha):
    return a + (b - a) * alpha


def interpolate_segment(a, b):
    sequence = []
    dt = b.tick - a.tick
    if dt <= 0:
        return sequence
    for tick in range(a.tick, b.tick + 1):
        alpha = (tick - a.tick) / dt
        sequence.append(
            ReconstructedTick(
                tick=tick,
                pos_x=lerp(a.pos_x, b.pos_x, alpha),
                pos_y=lerp(a.pos_y, b.pos_y, alpha),
                vel_x=lerp(a.vel_x, b.vel_x, alpha),
                vel_y=lerp(a.vel_y, b.vel_y, alpha),
                heading=lerp(a.heading, b.heading, alpha),
                energy=lerp(a.energy, b.energy, alpha),
                integrity=lerp(a.integrity, b.integrity, alpha),
                stress=lerp(a.stress, b.stress, alpha),
                fear=lerp(a.fear, b.fear, alpha),
                drive=lerp(a.drive, b.drive, alpha),
                confidence=1.0 - 0.5 * abs(alpha - 0.5),
                anchor=(tick == a.tick or tick == b.tick),
            )
        )
    return sequence

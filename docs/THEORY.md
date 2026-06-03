# Project BIOS

> Intelligent behavior emerging from the interaction of simple systems — inspired by biology, without copying it blindly.

---

## Core Philosophy

- **Embodiment First** — Cognition is deeply tied to the body and environment.
- **Internal Drives Over Scripts** — No behavior trees or hardcoded rules. Behavior arises from physiological needs and emotional signals.
- **Understandable Emergence** — We prioritize systems whose behavior can be explained and debugged.
- **Determinism** — Everything is reproducible for scientific experimentation.

---

## Homeostatic Drives

The agent is governed by three internal physiological variables:

| Variable | Role |
|---|---|
| **Energy** | Metabolic resource, consumed continuously |
| **Integrity** | Physical health, damaged by hazards |
| **Reserves** | Stored energy buffered from food |

As energy drops, `Drive` increases — pushing the agent toward food-seeking behavior naturally, without explicit "if hungry then seek food" rules.

### Drive Scaling

```python
drive = (MAX_ENERGY - current_energy) / MAX_ENERGY
# drive → 1.0 when starving, drive → 0.0 when satiated
```

---

## Affective System (Emotions)

The `EmotionHormoneEngine` translates body state and sensory input into three key signals. These act as **modulators** — influencing both goal selection and low-level motor commands.

| Signal | Trigger | Effect on Behavior |
|---|---|---|
| **Drive** | Low energy | Increases food-seeking priority |
| **Fear** | Hazard proximity | Strong avoidance + thrust boost |
| **Stress** | Wall proximity + damage | Modulates thrust, interrupts goals |

---

## Goal Arbitration

The **Goal Stack Manager (GSM)** implements persistent, interruptible behavior:

- Goals have a **priority** and a **persistence duration**
- Higher-priority goals (e.g. *Avoid Hazard* during high fear) can interrupt lower ones
- Prevents chaotic frame-by-frame behavioral switching

This creates stable, believable behavior compared to purely reactive systems.

---

## Memory Systems

### Semantic Memory — Cognitive Map
- Dead-reckoning odometry with landmark-based correction
- Sparse grid encoding hazard and food "place cells"
- Generates spatial bias vectors for planning

### Episodic Memory — Autobiographical
- Uses **Welford's online algorithm** to detect statistically surprising events
- Combines surprise with emotional intensity to decide what to store
- Records critical events: near-death, starvation, major recoveries

---

## Design Constraints (Intentional)

These are deliberate choices, not gaps:

- ✕ No neural networks *(yet)*
- ✕ No reinforcement learning *(yet)*
- ✕ No large language models

> Understanding how simple systems create complex behavior is more valuable at this stage than chasing benchmark scores.

---

## Roadmap

- [ ] Memory consolidation (episodic → semantic transfer)
- [ ] Intrinsic motivation / curiosity drive
- [ ] Hierarchical planning
- [ ] Value learning

---
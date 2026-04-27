# Project BIOS: Embodied Survival Simulation
**Intelligence as a byproduct of metabolic constraint.**

Project BIOS is an experimental AI framework where agent behavior is governed by internal homeostatic drives rather than pre-scripted logic or large language models. 

### Architecture
- **Physiological Layer (BST):** Tracks energy decay, physical integrity, and metabolic reserves.
- **Affective Layer (EHE):** Simulates stress and fear vectors that modulate decision-making.
- **Cognitive Layer (GSM):** A non-linear drive-selection engine using sigmoidal urgency curves.

### The Bridge
The "Mind" (Python) and "Body" (Godot Engine) communicate via a TCP socket bridge, allowing for a strict separation between cognitive logic and physical simulation.
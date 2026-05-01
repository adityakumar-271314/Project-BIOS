# Project BIOS: Embodied Survival Simulation
**Intelligence as a byproduct of metabolic constraint.**

Project BIOS is an experimental AI framework where agent behavior is governed by internal homeostatic drives rather than pre-scripted logic or large language models. 

## Quick Start
1. **Clone the repo:** `git clone https://github.com/adityakumar-271314/Project-BIOS.git`
2. **Start the Brain:** Run `python bridge.py` from the root directory.
3. **Start the Simulation:** Open the `simulation/Survival Sim` folder in Godot 4.x and press **F5** (Play).
4. **Observe:** Watch the Godot window for agent movement and visual representation of energy, integrity levels alongside stress value and current sction.


### Architecture
- **Physiological Layer (BST):** Tracks energy decay, physical integrity, and metabolic reserves.
- **Affective Layer (EHE):** Simulates stress and fear vectors that modulate decision-making.
- **Cognitive Layer (GSM):** A non-linear drive-selection engine.

### The Bridge
The "Mind" (Python) and "Body" (Godot Engine) communicate via a TCP socket bridge, allowing for a strict separation between cognitive logic and physical simulation.

> Note: This project is in it's very early stage of prototyping

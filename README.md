# Project BIOS
 
An embodied cognition simulation in which behavior emerges from physiology, emotion, memory, and environmental interaction, rather than from scripted behavior trees. The goal is understandable emergent intelligence built from first principles.
 
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Godot](https://img.shields.io/badge/Godot-4.x-478CBF?style=flat&logo=godot-engine&logoColor=white)](https://godotengine.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Status](https://img.shields.io/badge/Status-v0.1_Research_Prototype-orange)](https://github.com/adityakumar-271314/Project-BIOS)
 
Project BIOS is a Python and Godot embodied-agent research prototype for studying biologically inspired autonomous behavior. Agents act through internal drives rather than hardcoded decision logic.
 
[Features](#core-features) · [Architecture](#architecture) · [Installation](#installation) · [Roadmap](#roadmap) · [Documentation](#documentation)
 
## Simulation Preview
 
**Agent survival demo**
 
<img src="docs/media/project_bios_demo.gif" width="800" alt="Agent Survival Demo">

**Memory visualization**
 
<img src="docs/media/images/semantic_memory.png" width="800" alt="Memory Visualization">

**Telemetry dashboard**
 
<img src="docs/media/images/run_analysis.png" width="800" alt="Telemetry Dashboard">

## Core Features
 
### Embodied physiology
 
The agent tracks energy, integrity (health), motion expenditure, stress, and starvation penalties. Behavior follows from maintaining internal homeostasis rather than from a rule lookup table.
 
### Emotion-driven cognition
 
An emotion model converts body state and sensory input into three motivational signals: drive (hunger and resource-seeking), fear (threat response), and stress (generalized arousal). These signals modulate goal selection, steering intensity, action persistence, and how easily an ongoing action is interrupted.
 
### Persistent goal arbitration (GSM)
 
The Goal Stack Manager maintains stable behavioral intent, with explicit persistence and interruption rules governing when a goal is dropped in favor of another. Supported goals at present: wander, seek food, avoid hazard.
 
### Spatial memory system
 
Loosely modeled on hippocampal function, the agent maintains an internal cognitive map consisting of dead-reckoning odometry, landmark-based drift correction, a sparse decaying hazard/food grid, and a spatial bias term used in planning.
 
### Episodic autobiographical memory
 
The agent stores emotionally salient and statistically surprising experiences, using Welford's online variance algorithm to flag surprise. Stored episodes can be queried and used to inform future planning.
 
## Architecture
 
![Architecture Diagram](docs/architecture.svg)
 
### Cognitive pipeline
 
Each tick proceeds as follows: the Godot physics step produces sensor data, which crosses a TCP bridge into `Agent.tick()`. This updates the memory system and the emotion model, which feed the Goal Stack Manager. The selected goal is passed to the action dispatcher and its associated skills, producing a motor output that drives movement in Godot. Telemetry and replay data are logged at each step.
 
### Main subsystems
 
- `BodyStateTracker` — physiology and homeostasis
- `EmotionHormoneEngine` — drive, fear, stress
- `MemorySystem` — semantic and episodic memory
- `Brain` — Goal Stack Manager and action dispatcher (ADSE)

### Technical design principles
 
- **Deterministic.** Runs are fully reproducible and replayable, which makes debugging tractable.
- **Modular.** Subsystem boundaries are kept explicit so each component can be reasoned about, tested, and replaced independently.
- **Minimal complexity by default.** No LLMs, deep RL, or speculative abstractions are introduced until the simpler approach is shown to be insufficient.
- **First principles.** Behavior is treated as an emergent property of interacting simple systems, not as a target to be engineered directly.

## Repository Structure
 
```text
Project-BIOS/
├── core/                    # Cognition engine
│   ├── agent.py
│   ├── body.py
│   ├── emotions.py
│   ├── brain/
│   ├── memory/
│   └── ...
├── simulation/              # Godot 4.x project
├── tests/
├── tools/                   # Visualizer, etc.
├── docs/
└── bridge.py
```
 
## Installation
 
### Requirements
 
- Python 3.11+
- [Godot Engine 4.x](https://godotengine.org/download)
- `pip`

### Setup
 
```bash
git clone https://github.com/adityakumar-271314/Project-BIOS.git
cd Project-BIOS
 
pip install -r requirements.txt
```
 
### Running the simulation
 
**Step 1 — start the brain server**
 
```bash
python bridge.py
```
 
**Step 2 — run the Godot simulation**
 
1. Open `simulation/Survival Sim/project.godot` in Godot 4.x.
2. Press F5 to play.
3. The simulation connects to the Python brain automatically.

## Replay and Telemetry
 
Project BIOS records two logs per run: `telemetry.jsonl`, containing internal state at each tick, and `replay.jsonl`, containing the full deterministic replay data needed to reproduce a run exactly.
 
Tooling:
 
- **Semantic memory visualizer** (`tools/visualizer.py`) — post-mortem inspection of an agent's spatial recording.
- **Log visualizer** (`python tools/log_visualizer.py`) — parses `telemetry.jsonl` into multi-variable analytical plots.
- **Episodic memory renderer** — native engine-side playback inside Godot.

## Testing
 
```bash
pytest -v
```
 
## Known Limitations
 
Project BIOS is an early-stage research prototype (v0.1). The constraints below are intentional, to keep the current foundation small and legible:
 
- No long-term memory consolidation (episodic to semantic).
- Planning is reactive only; no multi-step goals yet.
- No learning or parameter adaptation.
- Environment objects are static.
- Simulation-only; ROS 2 and real-robot support are planned but not implemented.

## Roadmap
 
### v0.2 (planned)
 
- Memory-guided planning (avoiding past hazards, revisiting known food locations).
- Episodic memory influence on decision-making.
- Increased environmental complexity.
- Improved visualization tooling.


### Longer-term direction
 
- [ROS 2](https://docs.ros.org/en/rolling/) integration.
- Memory consolidation.
- Intrinsic motivation.
- Cognitive mapping improvements.

## Documentation
 
- [`docs/THEORY.md`](docs/THEORY.md) — theoretical foundations.
- [`docs/MEMORY_ARCHITECTURE.md`](docs/MEMORY_ARCHITECTURE.md) — memory system design.
- [`docs/HARDWARE.md`](docs/HARDWARE.md) — hardware integration notes.

## Contributing
 
Contributions and discussion are welcome. This is an experimental project; issues and pull requests are a reasonable way to raise questions or propose changes.
 
1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/my-feature`.
3. Commit changes: `git commit -m 'Add some feature'`.
4. Push the branch: `git push origin feature/my-feature`.
5. Open a pull request.

## License
 
This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.
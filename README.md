# Project BIOS

Project BIOS is a prototype embodied-agent simulation built with Python and Godot.
The agent operates using internal state variables such as energy, integrity,
stress, and environmental stimuli instead of scripted behavior trees.


##  Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/adityakumar-271314/Project-BIOS.git

cd Project-BIOS
```

## 2. Install Requirements
```bash
pip install -r requirements.txt
```

**Optional development tools:**

```bash
pip install pytest mypy
```

## 3. Start the Brain Server
Run the Python cognition process:

```bash
python bridge.py
```

**Expected Output:**
BIOS Brain Server active on 127.0.0.1:9999. Waiting for Godot...

## 4. Start the Simulation
1. Open the simulation/Survival Sim folder in Godot 4.x.

2. Press F5 (Play).

3. The Godot simulation will connect automatically to the Python brain.

## 5. Observe the Agent
The simulation visualizes the following real-time data:

- Agent movement

- Energy and integrity

- Stress levels

- Steering/thrust output

- Food seeking

- Hazard avoidance

- Spatial memory behavior

## Running Tests
Run all tests:

```bash
pytest -v
# or
python -m pytest -v
```
Run a single test file:

```bash
pytest tests/test_vectors.py -v
```

## Optional Static Type Checking
```bash
mypy core/
```

## Runtime Output
The simulation generates the following log files:

- telemetry.jsonl

- replay.jsonl

**These logs can be used for:**

[x] Replay analysis

[x] Debugging

[x] Deterministic validation

[x] Telemetry inspection


### Architecture
- **BodyStateTracker (BST):** Handles energy usage, integrity, reserves, and motion cost.
- **EmotionHormoneEngine (EHE):** Computes stress, fear, and hunger-driven urgency.
- **GoalStackManager (GSM):** Produces steering and thrust outputs from sensory input.
- **SpatialMemory:** Maintains internal odometry, landmarks, and sparse stimulus memory.

### The Bridge
The Python process and the Godot simulation communicate through a TCP socket bridge.
This keeps simulation logic and world physics separated while allowing deterministic message exchange.

> Note: This project is in it's very early stage of prototyping

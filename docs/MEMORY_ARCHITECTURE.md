# MEMORY_ARCHITECTURE.md

# Project BIOS — Memory Architecture

## Overview

The Project BIOS memory subsystem models several simplified cognitive functions inspired by biological memory systems.

The architecture is intentionally divided into multiple layers:

| Layer           | Responsibility                              |
| --------------- | ------------------------------------------- |
| Spatial Memory | Spatial cognition and environmental mapping |
| Episodic Memory | Autobiographical event encoding             |
| Memory System   | Unified facade and retrieval API            |

The design prioritizes:

* deterministic simulation behavior
* stable serialization
* low runtime overhead
* extensibility for future cognition research
* clean subsystem boundaries

The memory subsystem is fully deterministic under identical simulation inputs.

---

# High-Level Architecture

```text
Sensors
   ↓
MemorySystem.update()
   ├── SpatialMemory.update()
   └── EpisodicMemory.update()
```

The memory system receives sensor information once per simulation tick and distributes it to the appropriate subsystems.

---

# MemorySystem

Location:

```text
core/memory/memory_system.py
```

`MemorySystem` acts as the unified facade over all memory subsystems.

It owns:

* `SpatialMemory`
* `EpisodicMemory`

and exposes:

* update orchestration
* retrieval helpers
* serialization
* convenience accessors

This prevents higher-level systems from directly depending on internal subsystem implementation details.

---

# Spatial Memory

Location:

```text
core/memory/spatial_memory
```

Spatial memory functions as the agent's spatial cognition system.

It models:

* dead reckoning odometry
* landmark-based drift correction
* sparse environmental stimulus memory
* spatial bias generation

This subsystem is analogous to simplified hippocampal spatial mapping.

---

## Responsibilities

### 1. Internal Position Tracking

The system integrates acceleration over time to maintain:

* internal position
* internal velocity

using semi-implicit Euler integration.

---

### 2. Landmark Re-Zeroing

Visible landmarks are used to correct accumulated odometry drift.

Each landmark stores:

* estimated world position
* observation count
* last seen tick

Repeated observations increase confidence in the landmark.

---

### 3. Sparse Spatial Stimulus Grid

The world is represented as a sparse grid containing:

* hazard intensity
* food intensity

Each populated cell behaves similarly to a lightweight place-memory.

Grid cells decay over time using multiplicative fading.

---

### 4. Spatial Bias Generation

The planner can query nearby memory cells to generate steering influence vectors.

Hazard cells produce repulsion.

Food cells produce attraction.

This allows past environmental experiences to influence navigation.

---

# Episodic Memory

Location:

```text
core/memory/episodic.py
```

Episodic memory stores autobiographical experiences judged to be:

* statistically surprising
* emotionally salient
* physiologically critical

Unlike spatial memory, episodic memory is sparse and event-oriented.

---

# Episodic Event Model

Location:

```text
core/memory/schemas.py
```

Events are represented using the `EpisodicEvent` dataclass.

Each event stores:

* tick timestamp
* event classification
* significance score
* spatial location
* physiological state
* emotional state
* state deltas

The dataclass structure replaces earlier raw dictionary storage.

This improves:

* serialization stability
* type safety
* future maintainability
* retrieval consistency

---

# Event Encoding Pipeline

Each simulation tick:

```text
Current State
    ↓
Delta Calculation
    ↓
Statistical Surprise Estimation
    ↓
Emotional Weighting
    ↓
Significance Scoring
    ↓
Event Encoding Decision
```

---

## Statistical Surprise

The system uses Welford's online variance algorithm to estimate baseline behavioral statistics.

Tracked deltas include:

* energy
* integrity
* stress
* fear
* drive

Surprise is approximated using a z-score style metric:

```text
abs(value - mean) / std
```

This allows the agent to detect unusual experiences relative to its own history.

---

## Emotional Weighting

Significance is amplified using emotional intensity.

Current emotional weighting uses:

| Signal | Weight |
| ------ | ------ |
| Fear   | 0.5    |
| Stress | 0.3    |
| Drive  | 0.2    |

This biases memory formation toward emotionally important experiences.

---

# Critical Event Types

Certain physiological states bypass significance thresholds and force immediate encoding.

Current critical events:

* `near_death`
* `critical_starvation`

These are edge-triggered and only encode when entering the state.

---

# Standard Event Categories

Current episodic categories include:

* `damage_spike`
* `food_recovery`
* `hazard_encounter`
* `danger_state`
* `starvation_state`
* `high_significance`

These categories are generated dynamically from physiological and emotional conditions.

---

# Retrieval API

The `MemorySystem` facade exposes multiple retrieval methods.

---

## General Retrieval

### Recent Memories

```python
recall_recent(limit=10)
```

Returns the newest episodic events.

---

### Recall By Type

```python
recall_by_type(event_type)
```

Filters events by categorical type.

---

### Significant Memories

```python
recall_significant(min_significance=5.0)
```

Returns events above a significance threshold.

---

### Spatial Recall

```python
recall_near(pos_x, pos_y, radius)
```

Returns events near a spatial location.

Distance checks currently use squared Euclidean distance.

---

# Spatial Query Helpers

Higher-level helper methods simplify common cognitive queries.

Examples include:

```python
last_danger_event()
last_food_recovery()
most_significant_event()
nearby_danger_memories()
```

These helpers intentionally live in `MemorySystem` rather than inside `EpisodicMemory`.

This keeps subsystem responsibilities separated:

| Component      | Responsibility      |
| -------------- | ------------------- |
| EpisodicMemory | storage + encoding  |
| MemorySystem   | retrieval semantics |

---

# Serialization Architecture

Both spatial and episodic memory support full export/import serialization.

---

## Root Export Structure

```python
{
    "spatial": ...,
    "episodic": ...,
    "version": 1,
}
```

Versioning allows future migration compatibility.

---

# Spatial Serialization

Spatial memory exports:

* internal position
* internal velocity
* landmarks
* sparse stimulus grid
* internal tick counter

Sparse grid coordinates are serialized using string keys:

```text
"cx,cy"
```

This ensures JSON compatibility.

---

# Episodic Serialization

Episodic memory exports:

* internal tick counter
* all encoded events

Each event serializes using:

```python
event.to_dict()
```

Import reconstruction uses:

```python
EpisodicEvent.from_dict()
```

This preserves stable typed reconstruction.

---

# Determinism

A major design goal is deterministic simulation behavior.

The memory subsystem avoids:

* asynchronous mutation
* unordered iteration dependencies
* stochastic retrieval
* hidden side effects

All updates occur synchronously within the simulation tick.

---

# Current Design Philosophy

The architecture intentionally avoids premature complexity.

The system currently does NOT implement:

* neural embeddings
* vector databases
* semantic compression
* reinforcement learning
* threaded cognition
* long-term persistence daemons
* autonomous consolidation passes

The current implementation prioritizes:

* transparency
* inspectability
* extensibility
* simulation stability

---

# Planned Future Extensions

The architecture is designed to support future cognition features without major rewrites.

Potential future systems include:

---

## 1. Memory Degradation

Future versions may introduce:

* salience decay
* reinforcement through repetition
* memory fading curves

This is preferred over hard memory caps.

---

## 2. Episodic → Spatial Consolidation

Repeated episodic patterns may eventually compress into generalized semantic knowledge.

Example:

```text
Repeated hazard encounters
    ↓
Persistent environmental danger model
```

---

## 3. Memory-Influenced Planning

Future planners may directly query episodic memories during action selection.

Examples:

* avoid past trauma locations
* revisit successful food zones
* emotional steering bias

---

# Architectural Notes

The memory system is designed as a cognition research foundation rather than a biologically accurate simulation.

The implementation favors:

* modularity
* explainability
* deterministic behavior
* iterative evolution

over realism or scale.

This allows rapid experimentation while maintaining simulation reliability.

---
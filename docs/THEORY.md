# Design Notes

## Drive Scaling
The simulation uses normalized internal variables such as energy, integrity,
stress, and fear to influence movement behavior.

The current implementation increases urgency as energy decreases:

U = (MAX_ENERGY - energy) / MAX_ENERGY

This value influences food-seeking behavior.

## Stress Response
Stress is derived from:

- Integrity loss
- Proximity to walls
- Environmental hazards

Stress and fear modify steering and thrust outputs.

## Spatial Memory
The SpatialMemory system maintains:

- Dead-reckoning odometry
- Landmark correction
- Sparse hazard/food memory grids

This allows the agent to maintain a rough internal map without direct access
to world coordinates.
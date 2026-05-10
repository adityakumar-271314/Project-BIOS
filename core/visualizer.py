from __future__ import annotations
from typing import TYPE_CHECKING
import matplotlib.pyplot as plt
import matplotlib.patches as patches


if TYPE_CHECKING:
    from .hippocampus import SpatialMemory

def visualize_hippocampus(memory: SpatialMemory, title="Agent Mental Map"):
    """
    Renders the internal spatial memory grid and landmarks.
    Food: Green | Hazard: Red | Landmarks: Grey
    """
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # 1. Draw the Stimulus Grid
    for (cx, cy), cell in memory._grid.items():
        # Calculate world-space bounds for the cell
        x = cx * memory._cell_size
        y = cy * memory._cell_size
        
        # Determine color based on intensity
        # We blend Red (Hazard) and Green (Food)
        # Using alpha to show "strength" of memory
        if cell.hazard > 0 or cell.food > 0:
            color = [cell.hazard, cell.food, 0]  # RGB: Red=Hazard, Green=Food
            alpha = max(cell.hazard, cell.food)
            
            rect = patches.Rectangle(
                (x, y), memory._cell_size, memory._cell_size,
                linewidth=0, facecolor=color, alpha=min(alpha, 1.0)
            )
            ax.add_patch(rect)

    # 2. Draw Landmarks
    for lm_id, record in memory._landmarks.items():
        ax.scatter(
            record.pos.x, record.pos.y, 
            c='grey', marker='s', s=100, label='Landmark' if lm_id == 0 else ""
        )
        ax.annotate(f"LM_{lm_id}", (record.pos.x, record.pos.y), 
                    color='grey', fontsize=8, alpha=0.7)

    # 3. Final Agent Position
    ax.scatter(
        memory.internal_pos.x, memory.internal_pos.y, 
        c='blue', marker='P', s=200, label='Last Known Pos'
    )

    # Formatting
    ax.set_aspect('equal')
    ax.set_title(f"{title}\n{memory.debug_summary()}")
    ax.set_xlabel("World X")
    ax.set_ylabel("World Y")
    ax.grid(True, linestyle=':', alpha=0.4)
    
    # Create custom legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='s', color='w', label='Food', markerfacecolor='green', markersize=10),
        Line2D([0], [0], marker='s', color='w', label='Hazard', markerfacecolor='red', markersize=10),
        Line2D([0], [0], marker='s', color='w', label='Landmark', markerfacecolor='grey', markersize=10),
        Line2D([0], [0], marker='P', color='w', label='Deceased Loc', markerfacecolor='blue', markersize=10),
    ]
    ax.legend(handles=legend_elements, loc='upper right')

    plt.show()
"""
tools/log_visualizer.py

Post-run analysis tool for Project BIOS.
Analyzes telemetry.jsonl and replay.jsonl to help with debugging and demonstration.

Usage:
    python -m tools.log_visualizer                    # Show interactive plots
    python -m tools.log_visualizer --save analysis.png   # Save as image
"""

import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import matplotlib.pyplot as plt


@dataclass
class TelemetryFrame:
    tick: int
    energy: float
    integrity: float
    stress: float
    fear: float
    drive: float
    thrust: float
    steer: float
    pos_x: float
    pos_y: float
    velocity_x: float
    velocity_y: float
    landmark_count: int
    grid_cells: int


def load_telemetry(path: str = "telemetry.jsonl") -> List[TelemetryFrame]:
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    d = json.loads(line)
                    data.append(TelemetryFrame(**d))
                except Exception as e:
                    print(f"Warning: Skipping corrupted line: {e}")
    return data


def load_replay(path: str = "replay.jsonl"):
    frames = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    frames.append(json.loads(line))
                except:
                    pass
    return frames


def plot_telemetry(telemetry: List[TelemetryFrame], save_path: Optional[str] = None):
    """Generate comprehensive telemetry visualization"""
    if not telemetry:
        print("No telemetry data to plot.")
        return

    ticks = [t.tick for t in telemetry]

    fig, axs = plt.subplots(3, 2, figsize=(15, 11))
    fig.suptitle(
        "Project BIOS — Agent Performance Analysis", fontsize=18, fontweight="bold"
    )

    # 1. Vital Signs
    axs[0, 0].plot(
        ticks,
        [t.energy for t in telemetry],
        label="Energy",
        color="#2ca02c",
        linewidth=2,
    )
    axs[0, 0].plot(
        ticks,
        [t.integrity for t in telemetry],
        label="Integrity",
        color="#1f77b4",
        linewidth=2,
    )
    axs[0, 0].set_title("Energy & Integrity", fontweight="bold")
    axs[0, 0].legend()
    axs[0, 0].grid(True, alpha=0.3)

    # 2. Emotional State
    axs[0, 1].plot(
        ticks, [t.stress for t in telemetry], label="Stress", color="#d62728"
    )
    axs[0, 1].plot(ticks, [t.fear for t in telemetry], label="Fear", color="#ff7f0e")
    axs[0, 1].plot(
        ticks, [t.drive for t in telemetry], label="Drive (Hunger)", color="#9467bd"
    )
    axs[0, 1].set_title("Emotional / Motivational State", fontweight="bold")
    axs[0, 1].legend()
    axs[0, 1].grid(True, alpha=0.3)

    # 3. Motor Output
    axs[1, 0].plot(
        ticks, [t.thrust for t in telemetry], label="Thrust", color="#17becf"
    )
    axs[1, 0].plot(ticks, [t.steer for t in telemetry], label="Steer", color="#8c564b")
    axs[1, 0].set_title("Motor Commands", fontweight="bold")
    axs[1, 0].legend()
    axs[1, 0].grid(True, alpha=0.3)

    # 4. Trajectory
    axs[1, 1].plot(
        [t.pos_x for t in telemetry],
        [t.pos_y for t in telemetry],
        color="#1f77b4",
        linewidth=1.5,
        alpha=0.8,
    )
    axs[1, 1].set_title("Agent Internal Trajectory", fontweight="bold")
    axs[1, 1].set_xlabel("X Position")
    axs[1, 1].set_ylabel("Y Position")
    axs[1, 1].grid(True, alpha=0.3)

    # 5. Survival Score
    survival = [min(t.energy, t.integrity) for t in telemetry]
    axs[2, 0].plot(ticks, survival, color="darkred", linewidth=2.5)
    axs[2, 0].set_title("Survival Score (min(Energy, Integrity))", fontweight="bold")
    axs[2, 0].grid(True, alpha=0.3)

    # 6. Memory Growth
    axs[2, 1].plot(
        ticks, [t.landmark_count for t in telemetry], label="Landmarks", color="#e377c2"
    )
    axs[2, 1].plot(
        ticks, [t.grid_cells for t in telemetry], label="Grid Cells", color="#7f7f7f"
    )
    axs[2, 1].set_title("Memory System Growth", fontweight="bold")
    axs[2, 1].legend()
    axs[2, 1].grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"✅ Plot successfully saved as: {save_path}")
    else:
        plt.show()


def print_summary(telemetry, replay):
    print("\n" + "=" * 60)
    print("📊 PROJECT BIOS - SIMULATION SUMMARY")
    print("=" * 60)
    print(f"Total Ticks          : {len(telemetry)}")
    print(f"Final Energy         : {telemetry[-1].energy:.1f}")
    print(f"Final Integrity      : {telemetry[-1].integrity:.1f}")
    print(f"Max Landmarks        : {max(t.landmark_count for t in telemetry)}")
    print(f"Max Grid Cells       : {max(t.grid_cells for t in telemetry)}")

    if replay:
        last = replay[-1]
        mo = last.get("motor_output", {})
        print(
            f"Final Action         : Thrust={mo.get('thrust',0):.2f} | Steer={mo.get('steer',0):.2f}"
        )

    print("=" * 60)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Project BIOS Log Analyzer & Visualizer"
    )
    parser.add_argument(
        "--telemetry", default="telemetry.jsonl", help="Telemetry file path"
    )
    parser.add_argument("--replay", default="replay.jsonl", help="Replay file path")
    parser.add_argument(
        "--save", type=str, help="Save plot to this image file (e.g. run1_analysis.png)"
    )
    parser.add_argument(
        "--summary", action="store_true", help="Show only summary, no plot"
    )

    args = parser.parse_args()

    t_path = Path(args.telemetry)
    r_path = Path(args.replay)

    if not t_path.exists():
        print(f"❌ Error: Telemetry file not found: {t_path}")
        print("Make sure you ran a simulation first.")
        return

    print("🔄 Loading telemetry data...")
    telemetry = load_telemetry(str(t_path))
    print(f"✅ Loaded {len(telemetry)} frames")

    replay = []
    if r_path.exists():
        replay = load_replay(str(r_path))
        print(f"✅ Loaded {len(replay)} replay frames")

    print_summary(telemetry, replay)

    if args.summary:
        return

    print("📈 Generating visualization...")
    plot_telemetry(telemetry, args.save)


if __name__ == "__main__":
    main()

"""
tools/log_visualizer.py

Post-run analysis and 2D replay visualizer for Project BIOS.
Supports searching and selecting from run directories under /run_history/.

Usage:
    python -m tools.log_visualizer                     # Interactive run selector
    python -m tools.log_visualizer --run run000001     # Plot specific run
    python -m tools.log_visualizer --replay            # Launch Pygame 2D replay viewer
    python -m tools.log_visualizer --save chart.png    # Save plot as image
"""

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

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


def find_available_runs(base_dir: str = "run_history") -> List[Path]:
    path = Path(base_dir)
    if not path.exists():
        return []
    runs = [p for p in path.iterdir() if p.is_dir()]
    return sorted(runs, key=lambda x: x.name, reverse=True)


def select_run_interactively(runs: List[Path]) -> Optional[Path]:
    if not runs:
        print("❌ No runs found in 'run_history/'.")
        return None

    print("\n--- Project BIOS Runs Found ---")
    for idx, run_path in enumerate(runs):
        print(f" [{idx + 1}] {run_path.name}")
    print("-------------------------------")

    try:
        choice = int(input(f"Select a run (1-{len(runs)}): ")) - 1
        if 0 <= choice < len(runs):
            return runs[choice]
    except (ValueError, KeyboardInterrupt):
        pass

    print("Defaulting to latest run.")
    return runs[0]


def load_json_or_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []

    data = []
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []

        # Try loading as full JSON array first
        if content.startswith("["):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass

        # Fallback to JSONL line-by-line reading
        for line in content.splitlines():
            if line.strip():
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return data


def load_telemetry(file_path: Path) -> List[TelemetryFrame]:
    raw_data = load_json_or_jsonl(file_path)
    telemetry = []
    for d in raw_data:
        try:
            telemetry.append(TelemetryFrame(**d))
        except TypeError as e:
            continue
    return telemetry


def plot_telemetry(
    telemetry: List[TelemetryFrame], run_name: str, save_path: Optional[str] = None
):
    if not telemetry:
        print("❌ No valid telemetry data to plot.")
        return

    ticks = [t.tick for t in telemetry]

    # Dark mode theme setup
    plt.style.use("dark_background")
    fig, axs = plt.subplots(3, 2, figsize=(15, 10))
    fig.suptitle(
        f"Project BIOS — Performance Analysis [{run_name}]",
        fontsize=16,
        fontweight="bold",
        color="#e0e0e0",
    )

    grid_alpha = 0.2

    # 1. Vital Signs
    axs[0, 0].plot(
        ticks,
        [t.energy for t in telemetry],
        label="Energy",
        color="#4CAF50",
        linewidth=1.8,
    )
    axs[0, 0].plot(
        ticks,
        [t.integrity for t in telemetry],
        label="Integrity",
        color="#2196F3",
        linewidth=1.8,
    )
    axs[0, 0].set_title("Vital Signs", fontweight="bold", color="#ffffff")
    axs[0, 0].legend(loc="upper right")
    axs[0, 0].grid(True, alpha=grid_alpha)

    # 2. Emotional / Motivational State
    axs[0, 1].plot(
        ticks, [t.stress for t in telemetry], label="Stress", color="#F44336"
    )
    axs[0, 1].plot(ticks, [t.fear for t in telemetry], label="Fear", color="#FF9800")
    axs[0, 1].plot(
        ticks, [t.drive for t in telemetry], label="Drive (Hunger)", color="#9C27B0"
    )
    axs[0, 1].set_title("Affective Dynamics", fontweight="bold", color="#ffffff")
    axs[0, 1].legend(loc="upper right")
    axs[0, 1].grid(True, alpha=grid_alpha)

    # 3. Motor Output
    axs[1, 0].plot(
        ticks, [t.thrust for t in telemetry], label="Thrust", color="#00BCD4", alpha=0.8
    )
    axs[1, 0].plot(
        ticks, [t.steer for t in telemetry], label="Steer", color="#FFEB3B", alpha=0.8
    )
    axs[1, 0].set_title("Control Signals", fontweight="bold", color="#ffffff")
    axs[1, 0].legend(loc="upper right")
    axs[1, 0].grid(True, alpha=grid_alpha)

    # 4. Trajectory Map
    axs[1, 1].plot(
        [t.pos_x for t in telemetry],
        [t.pos_y for t in telemetry],
        color="#00E676",
        linewidth=1.2,
        alpha=0.85,
    )
    axs[1, 1].scatter(
        [telemetry[0].pos_x],
        [telemetry[0].pos_y],
        color="white",
        marker="o",
        label="Start",
    )
    axs[1, 1].scatter(
        [telemetry[-1].pos_x],
        [telemetry[-1].pos_y],
        color="red",
        marker="x",
        label="End",
    )
    axs[1, 1].set_title("Agent Spatial Trajectory", fontweight="bold", color="#ffffff")
    axs[1, 1].legend(loc="upper right")
    axs[1, 1].grid(True, alpha=grid_alpha)

    # 5. Survival Metric
    survival = [min(t.energy, t.integrity) for t in telemetry]
    axs[2, 0].plot(ticks, survival, color="#E91E63", linewidth=2.0)
    axs[2, 0].set_title(
        "Survival Score [min(Energy, Integrity)]", fontweight="bold", color="#ffffff"
    )
    axs[2, 0].grid(True, alpha=grid_alpha)

    # 6. Cognitive / Memory System
    axs[2, 1].plot(
        ticks, [t.landmark_count for t in telemetry], label="Landmarks", color="#FF4081"
    )
    axs[2, 1].plot(
        ticks, [t.grid_cells for t in telemetry], label="Grid Cells", color="#00E5FF"
    )
    axs[2, 1].set_title(
        "Internal World Representation", fontweight="bold", color="#ffffff"
    )
    axs[2, 1].legend(loc="upper left")
    axs[2, 1].grid(True, alpha=grid_alpha)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"✅ Plot successfully saved to: {save_path}")
    else:
        plt.show()


def run_pygame_replay(replay_frames: List[Dict[str, Any]]):
    """Renders a 2D interactive playback of the simulation environment using Pygame."""
    try:
        import pygame
    except ImportError:
        print(
            "❌ Pygame is not installed. Install it via 'pip install pygame' to view replays."
        )
        return

    if not replay_frames:
        print("❌ No replay data available to visualize.")
        return

    pygame.init()
    width, height = 1000, 800
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Project BIOS — 2D Replay Telemetry Viewer")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Consolas", 14)

    frame_idx = 0
    playing = True
    speed = 1

    # Find position range to dynamically center camera
    positions = [
        (f["sensor_packet"]["real_pos_x"], f["sensor_packet"]["real_pos_y"])
        for f in replay_frames
        if "sensor_packet" in f and "real_pos_x" in f["sensor_packet"]
    ]

    offset_x, offset_y = width // 2, height // 2
    if positions:
        avg_x = sum(p[0] for p in positions) / len(positions)
        avg_y = sum(p[1] for p in positions) / len(positions)
        offset_x -= avg_x
        offset_y -= avg_y

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    playing = not playing
                elif event.key == pygame.K_RIGHT:
                    frame_idx = min(len(replay_frames) - 1, frame_idx + 10)
                elif event.key == pygame.K_LEFT:
                    frame_idx = max(0, frame_idx - 10)
                elif event.key == pygame.K_UP:
                    speed = min(8, speed * 2)
                elif event.key == pygame.K_DOWN:
                    speed = max(1, speed // 2)

        if playing:
            frame_idx = (frame_idx + speed) % len(replay_frames)

        frame = replay_frames[frame_idx]
        sensor = frame.get("sensor_packet", {})
        motor = frame.get("motor_output", {})

        screen.fill((20, 24, 30))

        # Render Agent & Sensors
        if "real_pos_x" in sensor:
            ax = int(sensor["real_pos_x"] + offset_x)
            ay = int(sensor["real_pos_y"] + offset_y)
            rot = sensor.get("current_rotation", 0.0)

            # Draw sensed objects
            for obj in sensor.get("sensed_objects", []):
                dist = obj.get("dist", 0)
                angle = rot + obj.get("angle", 0)
                ox = int(ax + dist * math.cos(angle))
                oy = int(ay + dist * math.sin(angle))

                obj_type = obj.get("type", "")
                color = (
                    (255, 200, 0)
                    if obj_type == "food"
                    else (255, 50, 50) if obj_type == "hazard" else (150, 150, 255)
                )
                pygame.draw.line(screen, (50, 60, 70), (ax, ay), (ox, oy), 1)
                pygame.draw.circle(screen, color, (ox, oy), 5)

            # Draw Agent Body
            pygame.draw.circle(screen, (0, 230, 118), (ax, ay), 12)
            heading_x = int(ax + 20 * math.cos(rot))
            heading_y = int(ay + 20 * math.sin(rot))
            pygame.draw.line(
                screen, (255, 255, 255), (ax, ay), (heading_x, heading_y), 3
            )

        # Draw Telemetry Overlay
        hud = [
            f"Tick: {frame.get('tick', 0)} / {replay_frames[-1].get('tick', 0)}",
            f"Status: {'PLAYING' if playing else 'PAUSED'} (Speed: {speed}x)",
            f"Thrust: {motor.get('thrust', 0.0):.2f} | Steer: {motor.get('steer', 0.0):.2f}",
            f"Ray Central: {sensor.get('ray_c', 0):.2f} | Hazard Stim: {sensor.get('hazard_stim', 0):.2f}",
            "[SPACE] Pause | [LEFT/RIGHT] Seek | [UP/DOWN] Speed",
        ]

        for i, line in enumerate(hud):
            text = font.render(line, True, (220, 220, 220))
            screen.blit(text, (15, 15 + i * 20))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def print_summary(telemetry: List[TelemetryFrame], replay: List[Dict[str, Any]]):
    print("\n" + "=" * 60)
    print("📊 PROJECT BIOS — RUN SUMMARY")
    print("=" * 60)

    if telemetry:
        print(f"Total Telemetry Ticks : {len(telemetry)}")
        print(f"Final Energy          : {telemetry[-1].energy:.2f}")
        print(f"Final Integrity       : {telemetry[-1].integrity:.2f}")
        print(f"Max Landmarks         : {max(t.landmark_count for t in telemetry)}")
        print(f"Max Grid Cells        : {max(t.grid_cells for t in telemetry)}")

    if replay:
        print(f"Total Replay Frames   : {len(replay)}")
        last_mo = replay[-1].get("motor_output", {})
        print(
            f"Final Action          : Thrust={last_mo.get('thrust', 0):.2f} | Steer={last_mo.get('steer', 0):.2f}"
        )

    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Project BIOS Log Visualizer")
    parser.add_argument(
        "--run", type=str, help="Specific run folder name (e.g. run000001)"
    )
    parser.add_argument(
        "--dir", type=str, default="run_history", help="Base directory containing runs"
    )
    parser.add_argument("--save", type=str, help="Save plot output image path")
    parser.add_argument(
        "--replay",
        action="store_true",
        help="Launch interactive 2D Pygame Replay Visualizer",
    )
    parser.add_argument(
        "--summary", action="store_true", help="Display console summary only"
    )

    args = parser.parse_args()

    available_runs = find_available_runs(args.dir)

    selected_run_dir = None
    if args.run:
        selected_run_dir = Path(args.dir) / args.run
    elif len(available_runs) == 1:
        selected_run_dir = available_runs[0]
    elif available_runs:
        selected_run_dir = select_run_interactively(available_runs)

    if not selected_run_dir or not selected_run_dir.exists():
        print(f"❌ Target run directory not found.")
        sys.exit(1)

    print(f"📂 Loaded Run Target: {selected_run_dir.name}")

    t_path = selected_run_dir / "telemetry.json"
    if not t_path.exists():
        t_path = selected_run_dir / "telemetry.jsonl"

    r_path = selected_run_dir / "replay.json"
    if not r_path.exists():
        r_path = selected_run_dir / "replay.jsonl"

    telemetry = load_telemetry(t_path)
    replay = load_json_or_jsonl(r_path)

    print_summary(telemetry, replay)

    if args.summary:
        return

    if args.replay:
        run_pygame_replay(replay)
    else:
        plot_telemetry(telemetry, selected_run_dir.name, args.save)


if __name__ == "__main__":
    main()

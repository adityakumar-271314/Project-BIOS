from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
from ..data_loader import StorageDataLoader
from ..visuals.ascii_charts import AsciiCharts


class EpisodicReviewMode:
    """
    Provides an interactive terminal workflow to select a simulation run,
    browse its recorded episodes, and drill down into granular episode metadata,
    sizes, and keyframe metrics.
    """

    def __init__(self, data_loader: StorageDataLoader):
        self.loader = data_loader

    def run(self):
        runs = self.loader.discover_runs()
        if not runs:
            print("\n[!] No simulation runs or episodic memory directories found.")
            return

        while True:
            print(AsciiCharts.render_header("EPISODIC REVIEW MODE - RUN SELECTION"))
            print("Select a simulation run to inspect:")
            for idx, run_path in enumerate(runs):
                print(f"  [{idx + 1}] {run_path.name}")
            print("  [0] Exit to Main Menu")

            choice = input("\nEnter run number: ").strip()
            if choice == "0":
                break

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(runs):
                    self._inspect_run(runs[idx])
                else:
                    print("\n[!] Invalid run selection. Please try again.")
            except ValueError:
                print("\n[!] Please enter a valid numeric choice.")

    def _inspect_run(self, run_path: Path):
        summary = self.loader.get_run_summary(run_path)
        episodes = summary.get("episodes", [])

        if not episodes:
            print(f"\n[!] No episodes found in run: {summary['run_name']}")
            return

        while True:
            print(
                AsciiCharts.render_header(
                    f"RUN: {summary['run_name']} ({len(episodes)} Episodes)"
                )
            )

            headers = [
                "No.",
                "Episode Folder",
                "Event Type",
                "Duration",
                "Keyframes",
                "Size (Bytes)",
            ]
            rows = []
            for i, ep in enumerate(episodes):
                rows.append(
                    [
                        i + 1,
                        ep["episode_dir"],
                        ep["event_type"],
                        f"{ep['duration_ticks']:,}",
                        ep["keyframe_count"],
                        f"{ep['file_size_bytes']:,}",
                    ]
                )

            print(
                AsciiCharts.render_table(
                    headers, rows, title="Recorded Episodes Manifest"
                )
            )
            print(
                "\nEnter episode number to view deep telemetry/metadata details, or [0] to go back."
            )

            choice = input("\nEnter episode number: ").strip()
            if choice == "0":
                break

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(episodes):
                    self._inspect_episode(episodes[idx])
                else:
                    print("\n[!] Invalid episode selection.")
            except ValueError:
                print("\n[!] Please enter a valid numeric choice.")

    def _inspect_episode(self, ep: Dict[str, Any]):
        print(AsciiCharts.render_header(f"EPISODE DEEP DIVE: {ep['episode_dir']}"))
        details = [
            ("Episode Folder", ep["episode_dir"]),
            ("Event Type", ep["event_type"]),
            ("File Size", f"{ep['file_size_bytes']:,} bytes"),
            ("Start Tick", f"{ep['start_tick']:,}"),
            ("End Tick", f"{ep['end_tick']:,}"),
            ("Duration", f"{ep['duration_ticks']:,} ticks"),
            ("Keyframe Count", ep["keyframe_count"]),
            ("Peak Significance", f"{ep['peak_significance']:.4f}"),
        ]

        for label, val in details:
            print(f"  • {label.ljust(20)}: {val}")
        print("=" * 60)

        input("\nPress [Enter] to return to episode list...")

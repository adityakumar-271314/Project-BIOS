from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
from ..data_loader import StorageDataLoader
from ..visuals.ascii_charts import AsciiCharts


class RangeAnalysisMode:
    """
    Provides comparative analysis across a selected range of simulation runs [X, Y],
    visualizing scalability, total storage growth trends, and average metrics side-by-side.
    """

    def __init__(self, data_loader: StorageDataLoader):
        self.loader = data_loader

    def run(self):
        runs = self.loader.discover_runs()
        if not runs:
            print("\n[!] No simulation runs or episodic memory directories found.")
            return

        while True:
            print(AsciiCharts.render_header("MULTI-RUN RANGE ANALYSIS [X - Y]"))
            print(f"Available simulation runs ({len(runs)} total):")
            for idx, run_path in enumerate(runs):
                print(f"  [{idx + 1}] {run_path.name}")
            print("  [0] Return to Main Menu")

            if len(runs) < 1:
                break

            print("\nEnter the range of runs to compare (e.g., Start X to End Y).")
            start_choice = input("Enter start run number (X): ").strip()
            if start_choice == "0":
                break

            end_choice = input("Enter end run number (Y): ").strip()
            if end_choice == "0":
                break

            try:
                x = int(start_choice) - 1
                y = int(end_choice) - 1

                if 0 <= x < len(runs) and 0 <= y < len(runs):
                    if x > y:
                        x, y = y, x  # Normalize range order
                    self._analyze_range(runs[x : y + 1])
                else:
                    print("\n[!] Invalid run indices selected. Please check the range.")
            except ValueError:
                print("\n[!] Please enter valid numeric selections.")

    def _analyze_range(self, selected_runs: List[Path]):
        summaries = [
            (
                self.loader.load_run_summary(r)
                if hasattr(self.loader, "load_run_summary")
                else self.loader.get_run_summary(r)
            )
            for r in selected_runs
        ]

        print(
            AsciiCharts.render_header(
                f"RANGE COMPARISON REPORT ({len(selected_runs)} Runs Selected)"
            )
        )

        # 1. Comparative Data Table
        headers = [
            "Run Name",
            "Schema",
            "Episodes",
            "Total Size",
            "Avg Ep Size",
            "Avg Duration",
        ]
        rows = []
        for s in summaries:
            rows.append(
                [
                    s["run_name"],
                    f"v{s['schema_version']}",
                    s["total_episodes"],
                    f"{s['total_run_bytes']:,} B",
                    f"{s['avg_episode_bytes']:,} B",
                    f"{s['avg_duration_ticks']} t",
                ]
            )

        print(
            AsciiCharts.render_table(
                headers, rows, title="Comparative Range Summary Table"
            )
        )

        # 2. Storage Footprint Bar Chart Across Runs
        storage_trend = {s["run_name"]: s["total_run_bytes"] for s in summaries}
        print(
            AsciiCharts.render_bar_chart(
                storage_trend, title="Total Storage Footprint Trend Across Runs (Bytes)"
            )
        )

        # 3. Average Episode Size Bar Chart Across Runs
        avg_size_trend = {s["run_name"]: int(s["avg_episode_bytes"]) for s in summaries}
        print(
            AsciiCharts.render_bar_chart(
                avg_size_trend, title="Average Episode Size Across Runs (Bytes)"
            )
        )

        input("\nPress [Enter] to return to range selection...")

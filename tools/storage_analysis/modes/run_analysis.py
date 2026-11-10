from __future__ import annotations
from pathlib import Path
from ..data_loader import StorageDataLoader
from ..visuals.ascii_charts import AsciiCharts


class RunAnalysisMode:
    """
    Provides a deep-dive statistical and visual analysis of a single simulation run,
    displaying aggregate storage breakdown, size/duration distributions, and histograms.
    """

    def __init__(self, data_loader: StorageDataLoader):
        self.loader = data_loader

    def run(self):
        runs = self.loader.discover_runs()
        if not runs:
            print("\n[!] No simulation runs or episodic memory directories found.")
            return

        while True:
            print(AsciiCharts.render_header("SINGLE RUN DEEP-DIVE ANALYSIS"))
            print("Select a simulation run to analyze:")
            for idx, run_path in enumerate(runs):
                print(f"  [{idx + 1}] {run_path.name}")
            print("  [0] Return to Main Menu")

            choice = input("\nEnter run number: ").strip()
            if choice == "0":
                break

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(runs):
                    self._analyze_run(runs[idx])
                else:
                    print("\n[!] Invalid run selection. Please try again.")
            except ValueError:
                print("\n[!] Please enter a valid numeric choice.")

    def _analyze_run(self, run_path: Path):
        summary = self.loader.get_run_summary(run_path)
        episodes = summary.get("episodes", [])

        print(AsciiCharts.render_header(f"RUN METRICS: {summary['run_name']} (Schema v{summary['schema_version']})"))
        
        # Aggregate stats overview
        print(f"  • Total Storage Footprint : {summary['total_run_bytes']:,} bytes")
        print(f"    - Manifest File        : {summary['manifest_bytes']:,} bytes")
        print(f"    - Metadata Index       : {summary['index_bytes']:,} bytes")
        print(f"    - Episode Payloads     : {summary['payload_bytes']:,} bytes across {summary['total_episodes']} episodes")
        print(f"  • Episode Size (Bytes)   : Min={summary['min_episode_bytes']:,} | Max={summary['max_episode_bytes']:,} | Avg={summary['avg_episode_bytes']:,}")
        print(f"  • Episode Length (Ticks) : Min={summary['min_duration_ticks']:,} | Max={summary['max_duration_ticks']:,} | Avg={summary['avg_duration_ticks']}")

        if not episodes:
            print("\n[!] No episodes recorded in this run to display distributions.")
            input("\nPress [Enter] to continue...")
            return

        # 1. Storage breakdown bar chart
        storage_breakdown = {
            "Manifest": summary["manifest_bytes"],
            "Index": summary["index_bytes"],
            "Payloads": summary["payload_bytes"]
        }
        print(AsciiCharts.render_bar_chart(storage_breakdown, title="Storage Allocation Breakdown (Bytes)"))

        # 2. Episode size distribution histogram
        sizes = [ep["file_size_bytes"] for ep in episodes]
        print(AsciiCharts.render_histogram(sizes, bins=5, title="Episode Size Distribution (Bytes)"))

        # 3. Episode duration histogram
        durations = [ep["duration_ticks"] for ep in episodes]
        print(AsciiCharts.render_histogram(durations, bins=5, title="Episode Duration Distribution (Ticks)"))

        input("\nPress [Enter] to return to run selection...")
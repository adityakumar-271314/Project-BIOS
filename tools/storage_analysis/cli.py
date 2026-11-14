from __future__ import annotations
from pathlib import Path
import sys

from .data_loader import StorageDataLoader
from .visuals.ascii_charts import AsciiCharts
from .modes.episodic_review import EpisodicReviewMode
from .modes.run_analysis import RunAnalysisMode
from .modes.range_analysis import RangeAnalysisMode


class StorageAnalysisCLI:
    """
    Main interactive menu controller for the Episodic Memory Storage Analysis Tool Suite.
    Routes user selection to specific analysis modes.

    bash `python -m tools.storage_analysis.cli` to run the tool, optionally providing a custom root directory for episodic memory runs:
        python -m tools.storage_analysis.cli <custom_root_dir>
    """

    def __init__(self, root_dir: Path | str = "core/memory/episodes"):
        self.loader = StorageDataLoader(root_dir=root_dir)
        self.episodic_review = EpisodicReviewMode(self.loader)
        self.run_analysis = RunAnalysisMode(self.loader)
        self.range_analysis = RangeAnalysisMode(self.loader)

    def run(self):
        while True:
            print(AsciiCharts.render_header("EPISODIC MEMORY STORAGE ANALYSIS SUITE"))
            print("Select an analysis mode:")
            print(
                "  [1] Episodic Review Mode (Browse runs & inspect episode telemetry)"
            )
            print(
                "  [2] Single Run Deep-Dive Analysis (Aggregates, size & length distributions)"
            )
            print(
                "  [3] Multi-Run Range Analysis [X - Y] (Comparative scalability trends)"
            )
            print("  [0] Exit Tool")

            choice = input("\nEnter selection [0-3]: ").strip()

            if choice == "0":
                print("\nExiting Storage Analysis Tool. Goodbye!")
                break
            elif choice == "1":
                self.episodic_review.run()
            elif choice == "2":
                self.run_analysis.run()
            elif choice == "3":
                self.range_analysis.run()
            else:
                print("\n[!] Invalid selection. Please enter a number between 0 and 3.")


if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "run_history"
    cli = StorageAnalysisCLI(root_dir=target_dir)
    cli.run()

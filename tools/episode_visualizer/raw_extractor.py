import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

class RawTelemetryExtractor:
    def __init__(self, telemetry_file_path: str | Path):
        self.file_path = Path(telemetry_file_path)

    def extract_range(self, start_tick: int, end_tick: int) -> Tuple[List[Tuple[float, float]], Dict[int, Dict[str, float]]]:
        """
        Extracts raw telemetry positions and core metrics strictly between start_tick and end_tick.
        Returns a path list of (x, y) coordinates and a mapping of tick_id -> metric data.
        """
        raw_path: List[Tuple[float, float]] = []
        raw_metrics: Dict[int, Dict[str, float]] = {}

        if not self.file_path.exists():
            return raw_path, raw_metrics

        with open(self.file_path, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    tick_id = data.get("tick")
                    
                    if tick_id is None or not (start_tick <= tick_id <= end_tick):
                        continue

                    # Extract coordinates for mapping trajectory comparisons
                    if "pos_x" in data and "pos_y" in data:
                        raw_path.append((float(data["pos_x"]), float(data["pos_y"])))

                    # Extract core raw metric profiles for verification alignment
                    raw_metrics[tick_id] = {
                        "energy": float(data.get("energy", 1.0)),
                        "integrity": float(data.get("integrity", 1.0)),
                        "stress": float(data.get("stress", 0.0)),
                        "fear": float(data.get("fear", 0.0)),
                        "drive": float(data.get("drive", 0.0))
                    }
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue  # Safely bypass corrupted lines during structural checks

        return raw_path, raw_metrics
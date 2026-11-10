from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class StorageDataLoader:
    """
    Data layer for scanning, discovering, and parsing episodic memory runs,
    manifests, indices, and individual episode files under run_history/.
    """

    def __init__(self, root_dir: Path | str = "run_history"):
        self.root_dir = Path(root_dir)

    def discover_runs(self) -> List[Path]:
        """
        Scans for valid simulation run directories under run_history/.
        """
        runs = []
        if not self.root_dir.exists():
            return runs

        # If root itself is a run containing an episodes/ folder
        if (self.root_dir / "episodes").exists() or (self.root_dir / "manifest.json").exists():
            runs.append(self.root_dir)
        else:
            for sub_dir in sorted(self.root_dir.iterdir()):
                if sub_dir.is_dir() and sub_dir.name.startswith("run"):
                    runs.append(sub_dir)
        return runs

    def _get_episodes_dir(self, run_path: Path) -> Path:
        """Resolves the actual episodes directory within a run folder."""
        ep_sub = run_path / "episodes"
        if ep_sub.exists():
            return ep_sub
        return run_path

    def load_run_manifest(self, run_path: Path | str) -> Dict[str, Any]:
        ep_dir = self._get_episodes_dir(Path(run_path))
        path = ep_dir / "manifest.json"
        if not path.exists():
            return {"version": 2, "next_episode_id": 1}
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return {"version": 2, "next_episode_id": 1}

    def load_metadata_index(self, run_path: Path | str) -> Dict[str, Any]:
        ep_dir = self._get_episodes_dir(Path(run_path))
        path = ep_dir / "metadata_index.json"
        if not path.exists():
            return {"episodes": []}
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return {"episodes": []}

    def load_episode_details(self, episode_dir: Path | str) -> Dict[str, Any]:
        ep_path = Path(episode_dir)
        ep_file = ep_path / "episode.json"
        legacy_meta = ep_path / "metadata.json"

        ep_bytes = ep_file.stat().st_size if ep_file.exists() else 0
        if legacy_meta.exists():
            ep_bytes += legacy_meta.stat().st_size

        details = {
            "episode_dir": ep_path.name,
            "file_size_bytes": ep_bytes,
            "start_tick": 0,
            "end_tick": 0,
            "duration_ticks": 0,
            "keyframe_count": 0,
            "event_type": "unknown",
            "peak_significance": 0.0,
        }

        if ep_file.exists():
            try:
                with open(ep_file, "r") as f:
                    data = json.load(f)
                    start = data.get("start_tick", 0)
                    end = data.get("end_tick", 0)
                    details.update({
                        "start_tick": start,
                        "end_tick": end,
                        "duration_ticks": max(0, end - start),
                        "keyframe_count": len(data.get("key_frames", [])),
                        "event_type": data.get("event_type", "unknown"),
                        "peak_significance": data.get("peak_significance", 0.0),
                    })
            except Exception:
                pass

        return details

    def get_run_summary(self, run_path: Path | str) -> Dict[str, Any]:
        run_path = Path(run_path)
        ep_dir = self._get_episodes_dir(run_path)
        manifest = self.load_run_manifest(run_path)
        
        manifest_path = ep_dir / "manifest.json"
        index_path = ep_dir / "metadata_index.json"

        manifest_bytes = manifest_path.stat().st_size if manifest_path.exists() else 0
        index_bytes = index_path.stat().st_size if index_path.exists() else 0

        episode_dirs = sorted([d for d in ep_dir.iterdir() if d.is_dir() and d.name.startswith("episode")])
        
        episodes_data = [self.load_episode_details(d) for d in episode_dirs]
        total_payload_bytes = sum(e["file_size_bytes"] for e in episodes_data)

        sizes = [e["file_size_bytes"] for e in episodes_data]
        durations = [e["duration_ticks"] for e in episodes_data]

        return {
            "run_name": run_path.name,
            "schema_version": manifest.get("version", 2),
            "total_episodes": len(episode_dirs),
            "manifest_bytes": manifest_bytes,
            "index_bytes": index_bytes,
            "payload_bytes": total_payload_bytes,
            "total_run_bytes": manifest_bytes + index_bytes + total_payload_bytes,
            "max_episode_bytes": max(sizes) if sizes else 0,
            "min_episode_bytes": min(sizes) if sizes else 0,
            "avg_episode_bytes": round(total_payload_bytes / len(sizes), 2) if sizes else 0.0,
            "max_duration_ticks": max(durations) if durations else 0,
            "min_duration_ticks": min(durations) if durations else 0,
            "avg_duration_ticks": round(sum(durations) / len(durations), 2) if durations else 0.0,
            "episodes": episodes_data,
        }
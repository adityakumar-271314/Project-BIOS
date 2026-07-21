from pathlib import Path
from typing import List, Optional


class EpisodeBrowser:

    def __init__(self, root: Path | str = "run_history"):
        self.root = Path(root)

    def list_runs(self) -> List[Path]:
        """Discovers and returns all run directories inside run_history sorted by name."""
        if not self.root.exists():
            return []
        return sorted(
            [
                p
                for p in self.root.iterdir()
                if p.is_dir() and p.name.startswith("run")
            ]
        )

    def list_episodes(self, run_id: Optional[str] = None) -> List[Path]:
        """
        Lists episode directories within run_history/<run_id>/episodes/, 
        or across all runs if run_id is None.
        """
        if not self.root.exists():
            return []

        if run_id:
            episodes_dir = self.root / run_id / "episodes"
            if not episodes_dir.exists() or not episodes_dir.is_dir():
                return []
            return sorted(
                [
                    p
                    for p in episodes_dir.iterdir()
                    if p.is_dir() and p.name.startswith("episode")
                ]
            )

        episodes = []
        for run_dir in self.list_runs():
            episodes_dir = run_dir / "episodes"
            if episodes_dir.exists() and episodes_dir.is_dir():
                episodes.extend(
                    sorted(
                        [
                            p
                            for p in episodes_dir.iterdir()
                            if p.is_dir() and p.name.startswith("episode")
                        ]
                    )
                )
        return episodes

    def list(self, run_id: Optional[str] = None) -> List[Path]:
        """Alias for list_episodes to maintain backward compatibility."""
        return self.list_episodes(run_id=run_id)

    def latest(self, run_id: Optional[str] = None) -> Optional[Path]:
        episodes = self.list_episodes(run_id=run_id)
        if not episodes:
            return None
        return episodes[-1]
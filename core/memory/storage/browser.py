from pathlib import Path
class EpisodeBrowser:

    def __init__(self, root="run_history/run000001/episodes"):
        self.root = Path(root)

    def list(self):
        return sorted(
            [
                p
                for p in self.root.iterdir()
                if p.is_dir() and p.name.startswith("episode")
            ]
        )

    def latest(self):
        episodes = self.list()
        if not episodes:
            return None
        return episodes[-1]
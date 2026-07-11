from __future__ import annotations

import json
from pathlib import Path

from ..schemas import EpisodicEvent


class EpisodeLoader:

    def load(self, folder):

        folder = Path(folder)

        with open(folder / "episode.json", "r") as f:
            data = json.load(f)

        return EpisodicEvent.from_dict(data)

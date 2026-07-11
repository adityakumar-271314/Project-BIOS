import os
import pygame
from tools.episode_visualizer.config import AGENT_COLOR, AGENT_SIZE


class AssetManager:
    def __init__(self):
        self._cache = {}
        # Resolve the directory where assets.py lives: tools/episode_visualizer/
        self.base_path = os.path.dirname(os.path.abspath(__file__))

    def get_agent_sprite(self):
        if "agent" not in self._cache:
            # Construct absolute target path: tools/episode_visualizer/assets/agent.png
            image_path = os.path.join(self.base_path, "assets", "agent.png")

            try:
                if os.path.exists(image_path):
                    surf = pygame.image.load(image_path).convert_alpha()
                    # Scale to your config specifications
                    self._cache["agent"] = pygame.transform.scale(
                        surf, (AGENT_SIZE, AGENT_SIZE)
                    )
                else:
                    raise FileNotFoundError
            except Exception:
                fallback = pygame.Surface((AGENT_SIZE, AGENT_SIZE), pygame.SRCALPHA)
                pygame.draw.circle(
                    fallback,
                    AGENT_COLOR,
                    (AGENT_SIZE // 2, AGENT_SIZE // 2),
                    AGENT_SIZE // 2,
                )
                self._cache["agent"] = fallback

        return self._cache["agent"]

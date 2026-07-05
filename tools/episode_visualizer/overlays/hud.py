import pygame
from tools.episode_visualizer.config import HUD_FONT_SIZE, BLACK

class HUDOverlay:
    def __init__(self):
        self.font = pygame.font.SysFont(None, HUD_FONT_SIZE)

    def render(self, screen, session, playback, camera):
        if not session or not playback:
            return
            
        tick = playback.get_current_tick()
        if not tick:
            return
        
        # Access properties directly from the ReplayTick dataclass object
        lines = [
            f"Episode: {session.name}",
            f"Frame: {playback.current_frame}/{playback.total_frames - 1}",
            f"Tick Index: {tick.tick}",
            f"Playback Speed: {playback.speed:.1f}x",
            f"State Confidence: {tick.confidence:.2f}",
        ]
        
        for i, line in enumerate(lines):
            text = self.font.render(line, True, BLACK)
            screen.blit(text, (10, 10 + i * 22))
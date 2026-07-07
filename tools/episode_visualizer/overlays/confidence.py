import pygame
from tools.episode_visualizer.config import RED, BLUE

class ConfidenceOverlay:
    def __init__(self):
        self.visible = True

    def render(self, screen, session, playback, camera):
        if not self.visible or not session or not playback:
            return
            
        current_tick = playback.get_current_tick()
        if not current_tick:
            return

        # Render anchor points along the trajectory path
        for idx, t in enumerate(session.ticks):
            if t.anchor:
                pos = camera.world_to_screen(t.pos_x, t.pos_y)
                pygame.draw.circle(screen, BLUE, pos, 4)

        # Apply a visual degradation vignette layer if reconstruction confidence drops
        if current_tick.confidence < 1.0:
            alpha = int((1.0 - current_tick.confidence) * 180)  # Deeper overlay for low accuracy
            degrade_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            # Tint the borders or display frame slightly yellow/red to warn user
            pygame.draw.rect(degrade_surface, (255, 165, 0, alpha), degrade_surface.get_rect(), 4)
            screen.blit(degrade_surface, (0, 0))
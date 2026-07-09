import pygame
from tools.episode_visualizer.config import RED, BLUE

class ConfidenceOverlay:
    def __init__(self):
        self.visible = True

    def render(self, screen, session, playback, camera, ui=None):
        if not self.visible or not session or not playback:
            return
            
        current_tick = playback.get_current_tick()
        if not current_tick:
            return

        radius = ui.r(4) if ui else 4
        for t in session.ticks:
            if t.anchor:
                pos = camera.world_to_screen(t.pos_x, t.pos_y)
                pygame.draw.circle(screen, BLUE, pos, radius)

        if current_tick.confidence < 1.0:
            alpha = int((1.0 - current_tick.confidence) * 180)
            degrade_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            border_thickness = ui.w(4) if ui else 4
            pygame.draw.rect(degrade_surface, (255, 165, 0, alpha), degrade_surface.get_rect(), border_thickness)
            screen.blit(degrade_surface, (0, 0))
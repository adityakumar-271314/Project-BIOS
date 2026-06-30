import pygame
from tools.episode_visualizer.config import WINDOW_WIDTH, WINDOW_HEIGHT, TIMELINE_HEIGHT, DARK_GRAY, YELLOW

class GraphsOverlay:
    def __init__(self):
        self.visible = True
        self.font = pygame.font.SysFont(None, 16)

    def render(self, screen, session, playback, camera):
        if not self.visible or not session:
            return
            
        graph_y = WINDOW_HEIGHT - TIMELINE_HEIGHT - 120
        # Draw containment graph panel region boundary surface
        pygame.draw.rect(screen, DARK_GRAY, (0, graph_y, WINDOW_WIDTH, 120))
        
        tick = playback.get_current_tick() or {}
        
        # Output status indicators metric reading info
        status_text = (
            f"Metrics Panel -> Energy: {tick.get('energy', 0.0):.2f} | "
            f"Stress: {tick.get('stress', 0.0):.2f} | "
            f"Fear: {tick.get('fear', 0.0):.2f} | "
            f"Drive: {tick.get('drive', 0.0):.2f}"
        )
        
        text_surface = self.font.render(status_text, True, YELLOW)
        screen.blit(text_surface, (15, graph_y + 10))
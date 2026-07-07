import math
import pygame
from tools.episode_visualizer.config import RED

class HeadingOverlay:
    def __init__(self):
        self.visible = True

    def render(self, screen, session, playback, camera):
        if not self.visible:
            return
        tick = playback.get_current_tick()
        if not tick:
            return
            
        # Draw explicit heading line directly from current transformation state
        screen_pos = camera.world_to_screen(tick.pos_x, tick.pos_y)
        vector_length = 30
        
        end_x = screen_pos[0] + math.cos(tick.heading) * vector_length
        end_y = screen_pos[1] + math.sin(tick.heading) * vector_length
        
        pygame.draw.line(screen, RED, screen_pos, (int(end_x), int(end_y)), 3)
        pygame.draw.circle(screen, RED, (int(end_x), int(end_y)), 4)
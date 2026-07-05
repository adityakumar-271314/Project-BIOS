import pygame
from tools.episode_visualizer.config import WINDOW_WIDTH, WINDOW_HEIGHT, TIMELINE_HEIGHT, DARK_GRAY, WHITE, RED

class TimelineOverlay:
    def __init__(self):
        self.dragging = False
        self.y_top = WINDOW_HEIGHT - TIMELINE_HEIGHT

    def render(self, screen, session, playback, camera):
        if not session or playback.total_frames == 0:
            return
            
        # Draw base horizontal scrub track background layout block
        pygame.draw.rect(screen, (20, 20, 20), (0, self.y_top, WINDOW_WIDTH, TIMELINE_HEIGHT))
        pygame.draw.line(screen, DARK_GRAY, (0, self.y_top), (WINDOW_WIDTH, self.y_top), 2)
        
        # Calculate dynamic head positional ratio bounds
        progress = playback.current_frame / (playback.total_frames - 1) if playback.total_frames > 1 else 0
        scrub_x = int(progress * WINDOW_WIDTH)
        
        # Render clean slider tracks accenting tracking updates
        pygame.draw.rect(screen, RED, (0, self.y_top + (TIMELINE_HEIGHT // 2) - 2, scrub_x, 4))
        pygame.draw.rect(screen, DARK_GRAY, (scrub_x, self.y_top + (TIMELINE_HEIGHT // 2) - 2, WINDOW_WIDTH - scrub_x, 4))
        
        # Draw high-contrast tactile scrubbing knob handles
        knob_color = WHITE if not self.dragging else RED
        pygame.draw.circle(screen, knob_color, (scrub_x, self.y_top + (TIMELINE_HEIGHT // 2)), 8)

    def handle_event(self, event, playback):
        if playback.total_frames == 0:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mx, my = event.pos
                if my >= self.y_top:
                    self.dragging = True
                    self._seek_to_mouse(mx, playback)
                    return True
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
                return True
                
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mx, my = event.pos
                self._seek_to_mouse(mx, playback)
                return True
                
        return False

    def _seek_to_mouse(self, mouse_x: int, playback):
        ratio = max(0.0, min(1.0, mouse_x / WINDOW_WIDTH))
        target_frame = int(ratio * (playback.total_frames - 1))
        playback.seek(target_frame)
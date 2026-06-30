import pygame
from tools.episode_visualizer.config import WINDOW_WIDTH, WINDOW_HEIGHT, TIMELINE_HEIGHT, GRAY, WHITE

class TimelineOverlay:
    def __init__(self):
        self.dragging = False

    def render(self, screen, session, playback, camera):
        if not session or playback.total_frames == 0:
            return
            
        y = WINDOW_HEIGHT - TIMELINE_HEIGHT
        # Draw background tracker trackbar
        pygame.draw.rect(screen, GRAY, (0, y, WINDOW_WIDTH, TIMELINE_HEIGHT))
        
        # Calculate current progress marker position
        progress = playback.current_frame / (playback.total_frames - 1) if playback.total_frames > 1 else 0
        scrub_x = int(progress * WINDOW_WIDTH)
        
        # Render scrubbing handle indicator
        pygame.draw.rect(screen, WHITE, (scrub_x - 6, y, 12, TIMELINE_HEIGHT))

    def handle_event(self, event, playback):
        if playback.total_frames == 0:
            return False

        y_top = WINDOW_HEIGHT - TIMELINE_HEIGHT
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                mx, my = event.pos
                if my >= y_top:
                    self.dragging = True
                    self._seek_to_mouse(mx, playback)
                    return True
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
                
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
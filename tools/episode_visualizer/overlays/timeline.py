import pygame
from tools.episode_visualizer.config import TIMELINE_HEIGHT, DARK_GRAY, WHITE, RED


class TimelineOverlay:
    def __init__(self):
        self.dragging = False
        self.visible = True

    def render(self, screen, session, playback, camera, ui=None):
        if not self.visible or not session or playback.total_frames == 0:
            return

        screen_w, screen_h = screen.get_size()
        timeline_h = ui.h(TIMELINE_HEIGHT) if ui else TIMELINE_HEIGHT
        y_top = screen_h - timeline_h

        pygame.draw.rect(screen, (20, 20, 20), (0, y_top, screen_w, timeline_h))
        pygame.draw.line(
            screen, DARK_GRAY, (0, y_top), (screen_w, y_top), ui.w(2) if ui else 2
        )

        progress = (
            playback.current_frame / (playback.total_frames - 1)
            if playback.total_frames > 1
            else 0
        )
        scrub_x = int(progress * screen_w)

        track_y = (
            y_top + (timeline_h // 2) - ui.h(2) if ui else y_top + (timeline_h // 2) - 2
        )
        track_h = ui.h(4) if ui else 4

        pygame.draw.rect(screen, RED, (0, track_y, scrub_x, track_h))
        pygame.draw.rect(
            screen, DARK_GRAY, (scrub_x, track_y, screen_w - scrub_x, track_h)
        )

        knob_color = WHITE if not self.dragging else RED
        pygame.draw.circle(
            screen,
            knob_color,
            (scrub_x, y_top + (timeline_h // 2)),
            ui.r(8) if ui else 8,
        )

    def handle_event(self, event, playback):
        if playback.total_frames == 0:
            return False

        # Access runtime display dimensions directly from the active window context surface
        screen = pygame.display.get_surface()
        screen_w, screen_h = screen.get_size()

        # Approximate scaling factor down to local interaction handler geometry checks
        sy = screen_h / 800.0
        timeline_h = int(TIMELINE_HEIGHT * sy)
        y_top = screen_h - timeline_h

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mx, my = event.pos
                if my >= y_top:
                    self.dragging = True
                    self._seek_to_mouse(mx, screen_w, playback)
                    return True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mx, my = event.pos
                self._seek_to_mouse(mx, screen_w, playback)
                return True

        return False

    def _seek_to_mouse(self, mouse_x: int, screen_w: int, playback):
        ratio = max(0.0, min(1.0, mouse_x / screen_w))
        target_frame = int(ratio * (playback.total_frames - 1))
        playback.seek(target_frame)

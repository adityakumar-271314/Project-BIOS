import pygame

from tools.episode_visualizer.config import (
    BACKGROUND,
    DIVIDER_DARK,
    DIVIDER_LIGHT,
    ERROR_ACCENT,
    ERROR_BORDER,
    ERROR_GLOW,
    ERROR_RED,
    ERROR_SHADOW,
    PANEL_BG,
    TEXT,
    TEXT_MUTED,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from tools.episode_visualizer.scenes.base import Scene


class ErrorScene(Scene):
    def __init__(self, controller):
        super().__init__(controller)
        self.error_message = ""

    def on_enter(self, **kwargs):
        self.error_message = kwargs.get(
            "error_message",
            "Unknown Application Vector Abort Event.",
        )

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.controller.switch_to_scene("BROWSER")
            return True
        return False

    def render(self, screen: pygame.Surface):
        screen.fill(BACKGROUND)

        self.controller.ui.update(screen)
        ui = self.controller.ui

        panel_w = ui.w(780)
        panel_h = ui.h(300)
        panel_x = (ui.w(WINDOW_WIDTH) - panel_w) // 2
        panel_y = (ui.h(WINDOW_HEIGHT) - panel_h) // 2 - ui.h(20)

        pygame.draw.rect(
            screen,
            ERROR_SHADOW,
            (
                panel_x - ui.r(6),
                panel_y - ui.r(6),
                panel_w + ui.r(12),
                panel_h + ui.r(12),
            ),
            border_radius=ui.r(14),
        )

        pygame.draw.rect(
            screen,
            PANEL_BG,
            (panel_x, panel_y, panel_w, panel_h),
            border_radius=ui.r(12),
        )

        pygame.draw.rect(
            screen,
            ERROR_BORDER,
            (panel_x, panel_y, panel_w, panel_h),
            width=max(1, ui.r(3)),
            border_radius=ui.r(12),
        )

        pygame.draw.rect(
            screen,
            ERROR_ACCENT,
            (panel_x, panel_y, ui.w(10), panel_h),
            border_radius=ui.r(6),
        )

        pygame.draw.rect(
            screen,
            ERROR_GLOW,
            (
                panel_x + ui.w(2),
                panel_y + ui.h(8),
                ui.w(3),
                panel_h - ui.h(16),
            ),
            border_radius=ui.r(2),
        )

        title = self.controller.big_font.render(
            "CRITICAL VERIFICATION HALT",
            True,
            ERROR_RED,
        )
        screen.blit(title, (panel_x + ui.w(35), panel_y + ui.h(28)))

        pygame.draw.line(
            screen,
            DIVIDER_LIGHT,
            (panel_x + ui.w(30), panel_y + ui.h(72)),
            (panel_x + panel_w - ui.w(30), panel_y + ui.h(72)),
            max(1, ui.r(2)),
        )

        max_width = panel_w - ui.w(70)

        words = self.error_message.split()
        lines = []
        current = ""

        for word in words:
            test = current + (" " if current else "") + word
            if self.controller.font.size(test)[0] <= max_width:
                current = test
            else:
                lines.append(current)
                current = word

        if current:
            lines.append(current)

        y = panel_y + ui.h(95)

        for line in lines:
            txt = self.controller.font.render(line, True, TEXT)
            screen.blit(txt, (panel_x + ui.w(35), y))
            y += ui.h(32)

        pygame.draw.line(
            screen,
            DIVIDER_DARK,
            (panel_x + ui.w(30), panel_y + panel_h - ui.h(65)),
            (panel_x + panel_w - ui.w(30), panel_y + panel_h - ui.h(65)),
            max(1, ui.r(2)),
        )

        hint = self.controller.small_font.render(
            "Press ESC to return to the Episode Browser",
            True,
            TEXT_MUTED,
        )

        screen.blit(
            hint,
            hint.get_rect(
                center=(ui.w(WINDOW_WIDTH) // 2, panel_y + panel_h - ui.h(32))
            ),
        )

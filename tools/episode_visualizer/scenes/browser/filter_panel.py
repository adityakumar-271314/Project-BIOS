import pygame
from tools.episode_visualizer.config import (
    ACCENT_BLUE,
    ACCENT_CYAN,
    ERROR_RED,
    PANEL_BG,
    PANEL_BORDER,
    PANEL_BORDER_DARK,
    SELECT_GLOW,
    TEXT,
    TEXT_DIM,
    TEXT_WHITE,
    WINDOW_HEIGHT,
)


class FilterPanel:
    """Handles rendering and interaction logic for the left side filter panel."""

    def __init__(self, scene):
        self.scene = scene

    def get_chip_rect(self, i: int) -> pygame.Rect:
        ui = self.scene.controller.ui
        return pygame.Rect(ui.x(45), ui.y(160 + i * 36), ui.w(245), ui.h(28))

    def get_slider_rect(self) -> pygame.Rect:
        ui = self.scene.controller.ui
        return pygame.Rect(ui.x(45), ui.y(415), ui.w(245), ui.h(8))

    def get_tick_slider_rect(self) -> pygame.Rect:
        ui = self.scene.controller.ui
        return pygame.Rect(ui.x(45), ui.y(475), ui.w(245), ui.h(8))

    def is_in_reset_button(self, pos) -> bool:
        ui = self.scene.controller.ui
        panel_h = ui.h(WINDOW_HEIGHT) - ui.y(165)
        panel = pygame.Rect(ui.x(35), ui.y(110), ui.w(265), panel_h)
        reset_rect = pygame.Rect(
            panel.x + ui.w(12),
            panel.y + panel.height - ui.h(46),
            panel.width - ui.w(24),
            ui.h(34),
        )
        return reset_rect.collidepoint(pos)

    def handle_mouse_down(self, pos) -> bool:
        state = self.scene.state

        if self.is_in_reset_button(pos):
            state.reset_filters()
            self.scene.apply_filters()
            return True

        for i, et in enumerate(state.event_types):
            if self.get_chip_rect(i).collidepoint(pos):
                state.active_event_filter = (
                    None if state.active_event_filter == et else et
                )
                self.scene.apply_filters()
                return True

        if self.get_slider_rect().collidepoint(pos):
            state.dragging_slider = "sig"
            self.update_slider(pos)
            return True

        tick_rect = self.get_tick_slider_rect()
        if tick_rect.inflate(0, 10).collidepoint(pos):
            rel_x = (pos[0] - tick_rect.x) / tick_rect.width
            tick_range = state.max_repository_ticks - state.min_repository_ticks
            val = state.min_repository_ticks + int(rel_x * tick_range)

            if abs(val - state.tick_start) < abs(val - state.tick_end):
                state.dragging_slider = "tick_start"
            else:
                state.dragging_slider = "tick_end"
            self.update_slider(pos)
            return True

        return False

    def update_slider(self, pos):
        state = self.scene.state
        tick_range = state.max_repository_ticks - state.min_repository_ticks

        if state.dragging_slider == "sig":
            slider_rect = self.get_slider_rect()
            rel_x = max(0.0, min(1.0, (pos[0] - slider_rect.x) / slider_rect.width))
            state.min_peak_significance = int(rel_x * 100)
        elif state.dragging_slider in ("tick_start", "tick_end"):
            tick_rect = self.get_tick_slider_rect()
            rel_x = max(0.0, min(1.0, (pos[0] - tick_rect.x) / tick_rect.width))
            val = state.min_repository_ticks + int(rel_x * tick_range)
            if state.dragging_slider == "tick_start":
                state.tick_start = max(
                    state.min_repository_ticks, min(val, state.tick_end - 1)
                )
            else:
                state.tick_end = max(
                    state.tick_start + 1, min(val, state.max_repository_ticks)
                )
        self.scene.apply_filters()

    def render(self, screen: pygame.Surface):
        ui = self.scene.controller.ui
        state = self.scene.state

        panel_h = ui.h(WINDOW_HEIGHT) - ui.y(165)
        panel = pygame.Rect(ui.x(35), ui.y(110), ui.w(265), panel_h)
        pygame.draw.rect(screen, PANEL_BG, panel, border_radius=ui.r(8))
        pygame.draw.rect(
            screen, PANEL_BORDER, panel, width=max(1, ui.r(1)), border_radius=ui.r(8)
        )

        y = panel.y + ui.h(14)
        screen.blit(
            self.scene.controller.font.render("EVENT CATEGORIES", True, ACCENT_CYAN),
            (panel.x + ui.w(12), y),
        )

        for i, et in enumerate(state.event_types):
            rect = self.get_chip_rect(i)
            is_active = state.active_event_filter == et
            color = ACCENT_CYAN if is_active else TEXT_DIM
            bg = SELECT_GLOW if is_active else PANEL_BORDER_DARK

            pygame.draw.rect(screen, bg, rect, border_radius=ui.r(6))
            if is_active:
                pygame.draw.rect(
                    screen,
                    ACCENT_CYAN,
                    rect,
                    width=max(1, ui.r(1)),
                    border_radius=ui.r(6),
                )

            txt = self.scene.controller.small_font.render(
                et.replace("_", " ").upper(), True, color
            )
            screen.blit(
                txt,
                (
                    rect.x + ui.w(10),
                    rect.y + (rect.height // 2 - txt.get_height() // 2),
                ),
            )

        slider_rect = self.get_slider_rect()
        y_slider_lbl = slider_rect.y - ui.h(22)
        screen.blit(
            self.scene.controller.small_font.render(
                f"MIN SIGNIFICANCE: {state.min_peak_significance}/100", True, TEXT
            ),
            (panel.x + ui.w(12), y_slider_lbl),
        )

        pygame.draw.rect(screen, PANEL_BORDER_DARK, slider_rect, border_radius=ui.r(4))
        fill_w = int(slider_rect.width * (state.min_peak_significance / 100))
        if fill_w > 0:
            pygame.draw.rect(
                screen,
                ACCENT_CYAN,
                (slider_rect.x, slider_rect.y, fill_w, slider_rect.height),
                border_radius=ui.r(4),
            )

        tick_rect = self.get_tick_slider_rect()
        y_tick_lbl = tick_rect.y - ui.h(22)
        screen.blit(
            self.scene.controller.small_font.render(
                f"TICK RANGE: {state.tick_start} - {state.tick_end}", True, TEXT
            ),
            (panel.x + ui.w(12), y_tick_lbl),
        )

        pygame.draw.rect(screen, PANEL_BORDER_DARK, tick_rect, border_radius=ui.r(4))

        tick_range = state.max_repository_ticks - state.min_repository_ticks
        denom = tick_range if tick_range > 0 else 1
        start_x = tick_rect.x + int(
            tick_rect.width * ((state.tick_start - state.min_repository_ticks) / denom)
        )
        end_x = tick_rect.x + int(
            tick_rect.width * ((state.tick_end - state.min_repository_ticks) / denom)
        )

        if end_x > start_x:
            pygame.draw.rect(
                screen,
                ACCENT_BLUE,
                (start_x, tick_rect.y, end_x - start_x, tick_rect.height),
                border_radius=ui.r(4),
            )

        pygame.draw.circle(
            screen, TEXT_WHITE, (start_x, tick_rect.y + tick_rect.height // 2), ui.r(6)
        )
        pygame.draw.circle(
            screen, TEXT_WHITE, (end_x, tick_rect.y + tick_rect.height // 2), ui.r(6)
        )

        reset_rect = pygame.Rect(
            panel.x + ui.w(12),
            panel.y + panel.height - ui.h(46),
            panel.width - ui.w(24),
            ui.h(34),
        )
        pygame.draw.rect(screen, ERROR_RED, reset_rect, border_radius=ui.r(6))
        reset_txt = self.scene.controller.small_font.render(
            "RESET ALL FILTERS", True, TEXT_WHITE
        )
        screen.blit(reset_txt, reset_txt.get_rect(center=reset_rect.center))

import pygame

from core.memory.storage.browser import EpisodeBrowser
from tools.episode_visualizer.config import (
    ACCENT_BLUE,
    ACCENT_CYAN,
    ACCENT_CYAN_DIM,
    BACKGROUND,
    DIVIDER_DARK,
    ERROR_RED,
    PANEL_BG,
    PANEL_BORDER,
    PANEL_BORDER_DARK,
    PANEL_HIGHLIGHT,
    ROW_ALT_BG,
    SELECT_ARROW,
    SELECT_BAR,
    SELECT_GLOW,
    TEXT_DIM,
    TEXT_FOOTER,
    TEXT_MUTED,
    TEXT_WHITE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from tools.episode_visualizer.replay_loader import load_from_storage
from tools.episode_visualizer.scenes.base import Scene


class BrowserScene(Scene):
    def __init__(self, controller):
        super().__init__(controller)
        self.browser_util = EpisodeBrowser()
        self.episodes_list = []
        self.selected_idx = 0
        self.refresh_browser_list()

    def on_enter(self, **kwargs):
        self.refresh_browser_list()

    def refresh_browser_list(self):
        try:
            self.episodes_list = self.browser_util.list()
            self.selected_idx = 0
        except Exception as e:
            self.controller.trigger_error(f"Failed listing target paths: {e}")

    def handle_event(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return False

        if event.key == pygame.K_UP:
            self.selected_idx = max(0, self.selected_idx - 1)

        elif event.key == pygame.K_DOWN:
            self.selected_idx = min(
                len(self.episodes_list) - 1,
                self.selected_idx + 1,
            )

        elif event.key == pygame.K_RETURN and self.episodes_list:
            try:
                target_folder = self.episodes_list[self.selected_idx]
                session = load_from_storage(target_folder)
                self.controller.switch_to_scene("PLAYBACK", session=session)
            except Exception as e:
                self.controller.trigger_error(f"Reconstruction Halt Constraint: {e}")

        return True

    def render(self, screen: pygame.Surface):
        screen.fill(BACKGROUND)

        self.controller.ui.update(screen)
        ui = self.controller.ui
        
        if not self.episodes_list:
            title = self.controller.big_font.render(
                "EMPTY REPOSITORY", True, ERROR_RED
            )
            msg = self.controller.font.render(
                "No playable episodes were discovered.",
                True,
                TEXT_MUTED,
            )
            hint = self.controller.font.render(
                "Press F1 for Help",
                True,
                TEXT_DIM,
            )

            screen.blit(title, title.get_rect(center=(ui.w(WINDOW_WIDTH) // 2, ui.h(WINDOW_HEIGHT) // 2 - ui.h(50))))
            screen.blit(msg, msg.get_rect(center=(ui.w(WINDOW_WIDTH) // 2, ui.h(WINDOW_HEIGHT) // 2)))
            screen.blit(hint, hint.get_rect(center=(ui.w(WINDOW_WIDTH) // 2, ui.h(WINDOW_HEIGHT) // 2 + ui.h(45))))
            return

        title = self.controller.big_font.render(
            "SYSTEM EPISODE BROWSER",
            True,
            ACCENT_CYAN,
        )
        screen.blit(title, (ui.x(40), ui.y(25)))

        controls = self.controller.small_font.render(
            "↑↓ Navigate    ENTER Load Episode    F1 Help    ESC Exit",
            True,
            TEXT_MUTED,
        )
        screen.blit(controls, (ui.x(40), ui.y(78)))

        pygame.draw.line(
            screen,
            ACCENT_CYAN_DIM,
            (ui.x(40), ui.y(68)),
            (ui.w(WINDOW_WIDTH) - ui.x(40), ui.y(68)),
            max(1, ui.r(3)),
        )
        pygame.draw.line(
            screen,
            ACCENT_CYAN,
            (ui.x(40), ui.y(70)),
            (ui.w(WINDOW_WIDTH) - ui.x(40), ui.y(70)),
            1,
        )

        panel_x = ui.x(35)
        panel_y = ui.y(115)
        panel_w = ui.w(WINDOW_WIDTH) - ui.x(70)
        panel_h = ui.h(WINDOW_HEIGHT) - ui.y(165)

        pygame.draw.rect(
            screen,
            PANEL_BORDER_DARK,
            (
                panel_x - ui.r(3),
                panel_y - ui.r(3),
                panel_w + ui.r(6),
                panel_h + ui.r(6),
            ),
            border_radius=ui.r(12),
        )

        pygame.draw.rect(
            screen,
            PANEL_BG,
            (panel_x, panel_y, panel_w, panel_h),
            border_radius=ui.r(10),
        )

        pygame.draw.rect(
            screen,
            PANEL_BORDER,
            (panel_x, panel_y, panel_w, panel_h),
            width=max(1, ui.r(2)),
            border_radius=ui.r(10),
        )

        pygame.draw.rect(
            screen,
            PANEL_HIGHLIGHT,
            (
                panel_x + ui.r(4),
                panel_y + ui.r(4),
                panel_w - ui.r(8),
                ui.r(4),
            ),
            border_radius=ui.r(6),
        )

        row_height = ui.h(38)
        visible_rows = min(
            len(self.episodes_list),
            max(0, (panel_h - ui.h(30)) // row_height),
        )

        for idx in range(visible_rows):
            path = self.episodes_list[idx]
            y = panel_y + ui.h(18) + idx * row_height
            selected = idx == self.selected_idx

            row_rect = (
                panel_x + ui.w(8),
                y - ui.h(4),
                panel_w - ui.w(16),
                row_height - ui.h(4),
            )

            if idx % 2 == 0:
                pygame.draw.rect(
                    screen,
                    ROW_ALT_BG,
                    row_rect,
                    border_radius=ui.r(6),
                )

            if selected:
                pygame.draw.rect(
                    screen,
                    SELECT_GLOW,
                    row_rect,
                    border_radius=ui.r(6),
                )

                pygame.draw.rect(
                    screen,
                    SELECT_BAR,
                    (
                        panel_x + ui.w(8),
                        y - ui.h(4),
                        ui.w(6),
                        row_height - ui.h(4),
                    ),
                    border_radius=ui.r(3),
                )

                pygame.draw.polygon(
                    screen,
                    SELECT_ARROW,
                    [
                        (panel_x + ui.w(26), y + ui.h(12)),
                        (panel_x + ui.w(38), y + ui.h(7)),
                        (panel_x + ui.w(38), y + ui.h(19)),
                    ],
                )

                text_color = TEXT_WHITE
            else:
                text_color = TEXT_DIM

            index_text = self.controller.font.render(
                f"{idx + 1:02d}.",
                True,
                ACCENT_BLUE,
            )
            screen.blit(index_text, (panel_x + ui.w(48), y + ui.h(2)))

            name_text = self.controller.font.render(
                path.name,
                True,
                text_color,
            )
            screen.blit(name_text, (panel_x + ui.w(105), y + ui.h(2)))

        footer_y = ui.h(WINDOW_HEIGHT) - ui.y(48)

        pygame.draw.line(
            screen,
            DIVIDER_DARK,
            (ui.x(35), footer_y),
            (ui.w(WINDOW_WIDTH) - ui.x(35), footer_y),
            max(1, ui.r(2)),
        )

        footer = self.controller.small_font.render(
            f"EPISODES FOUND : {len(self.episodes_list)}",
            True,
            TEXT_FOOTER,
        )

        screen.blit(footer, (ui.x(42), footer_y + ui.y(12)))
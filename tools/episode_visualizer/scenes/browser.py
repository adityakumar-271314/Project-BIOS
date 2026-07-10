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
        except FileNotFoundError:
            self.episodes_list = []
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
        
        # --- Empty State UI View ---
        if not self.episodes_list:
            title = self.controller.big_font.render("EMPTY REPOSITORY", True, ERROR_RED)
            msg = self.controller.font.render("No playable episodes were discovered.", True, TEXT_MUTED)
            hint = self.controller.font.render("Press F1 for Help", True, TEXT_DIM)

            screen.blit(title, title.get_rect(center=(ui.w(WINDOW_WIDTH) // 2, ui.h(WINDOW_HEIGHT) // 2 - ui.h(50))))
            screen.blit(msg, msg.get_rect(center=(ui.w(WINDOW_WIDTH) // 2, ui.h(WINDOW_HEIGHT) // 2)))
            screen.blit(hint, hint.get_rect(center=(ui.w(WINDOW_WIDTH) // 2, ui.h(WINDOW_HEIGHT) // 2 + ui.h(45))))
            return

        # --- Premium Header Layout Section ---
        title = self.controller.big_font.render("SYSTEM EPISODE BROWSER", True, ACCENT_CYAN)
        screen.blit(title, (ui.x(40), ui.y(25)))

        controls = self.controller.small_font.render(
            "↑↓ Navigate    ENTER Load Episode    F1 Help    ESC Exit", True, TEXT_MUTED
        )
        screen.blit(controls, (ui.x(40), ui.y(74)))

        # Clean, unified header bounding line accents
        pygame.draw.line(
            screen,
            ACCENT_CYAN_DIM,
            (ui.x(40), ui.y(64)),
            (ui.w(WINDOW_WIDTH) - ui.x(40), ui.y(64)),
            max(1, ui.r(1)),
        )

        # --- Main Viewport Control Panel Configuration ---
        panel_x = ui.x(35)
        panel_y = ui.y(110)
        panel_w = ui.w(WINDOW_WIDTH) - ui.x(70)
        panel_h = ui.h(WINDOW_HEIGHT) - ui.y(165)

        # Ambient Shadow Border
        pygame.draw.rect(
            screen,
            PANEL_BORDER_DARK,
            (panel_x - ui.r(2), panel_y - ui.r(2), panel_w + ui.r(4), panel_h + ui.r(4)),
            border_radius=ui.r(10),
            width=max(1, ui.r(1))
        )

        # Solid Control Panel Base Canvas
        pygame.draw.rect(screen, PANEL_BG, (panel_x, panel_y, panel_w, panel_h), border_radius=ui.r(8))
        pygame.draw.rect(screen, PANEL_BORDER, (panel_x, panel_y, panel_w, panel_h), width=max(1, ui.r(1)), border_radius=ui.r(8))

        # Top Neon Line Accent Plate
        pygame.draw.rect(
            screen,
            PANEL_HIGHLIGHT,
            (panel_x + ui.r(2), panel_y + ui.r(2), panel_w - ui.r(4), ui.r(3)),
            border_radius=ui.r(2),
        )

        # --- Dynamic Scroll Window Layout Engine ---
        row_height = ui.h(42)  # Increased height padding for breathing room
        visible_rows = max(1, (panel_h - ui.h(24)) // row_height)
        
        # Calculate sliding scroll offset based on selected row placement
        start_idx = 0
        if len(self.episodes_list) > visible_rows:
            start_idx = max(0, min(self.selected_idx - visible_rows // 2, len(self.episodes_list) - visible_rows))
        end_idx = min(start_idx + visible_rows, len(self.episodes_list))

        # --- Render Data Row Set ---
        for render_slot, idx in enumerate(range(start_idx, end_idx)):
            path = self.episodes_list[idx]
            y_pos = panel_y + ui.h(12) + render_slot * row_height
            selected = (idx == self.selected_idx)

            row_rect = pygame.Rect(
                panel_x + ui.w(10),
                y_pos,
                panel_w - ui.w(20),
                row_height - ui.h(4)
            )

            # Zebra Striping Layout
            if idx % 2 == 0 and not selected:
                pygame.draw.rect(screen, ROW_ALT_BG, row_rect, border_radius=ui.r(6))

            # Selected Accent State
            if selected:
                # Translucent Selection Plate Glow
                pygame.draw.rect(screen, SELECT_GLOW, row_rect, border_radius=ui.r(6))
                
                # Solid Left-Hand Navigation Anchor Node Bar
                pygame.draw.rect(
                    screen,
                    SELECT_BAR,
                    (row_rect.x, row_rect.y, ui.w(4), row_rect.height),
                    border_radius=ui.r(2),
                )

                # Modern Selection Indicator Arrow Vector
                arrow_center_y = row_rect.y + row_rect.height // 2
                pygame.draw.polygon(
                    screen,
                    SELECT_ARROW,
                    [
                        (panel_x + ui.w(24), arrow_center_y),
                        (panel_x + ui.w(32), arrow_center_y - ui.h(5)),
                        (panel_x + ui.w(32), arrow_center_y + ui.h(5)),
                    ],
                )
                text_color = TEXT_WHITE
                text_padding_offset = ui.w(10)  # Micro-interaction text shift on selection
            else:
                text_color = TEXT_DIM
                text_padding_offset = 0

            # Unique Index Tag Render Column
            index_text = self.controller.font.render(f"{idx + 1:02d}.", True, ACCENT_BLUE)
            screen.blit(index_text, (panel_x + ui.w(44) + text_padding_offset, y_pos + (row_rect.height // 2) - (index_text.get_height() // 2)))

            # Truncate paths that are too long to prevent row layout breakage
            max_chars = int(panel_w // ui.w(14))
            display_name = path.name if len(path.name) <= max_chars else f"{path.name[:max_chars-3]}..."
            
            name_text = self.controller.font.render(display_name, True, text_color)
            screen.blit(name_text, (panel_x + ui.w(95) + text_padding_offset, y_pos + (row_rect.height // 2) - (name_text.get_height() // 2)))

        # --- Bottom Console Panel Footer Assembly ---
        footer_y = ui.h(WINDOW_HEIGHT) - ui.y(42)

        pygame.draw.line(
            screen,
            DIVIDER_DARK,
            (ui.x(35), footer_y),
            (ui.w(WINDOW_WIDTH) - ui.x(35), footer_y),
            max(1, ui.r(1)),
        )

        footer = self.controller.small_font.render(
            f"SYSTEM REPOSITORY REPLAYS AVAILABLE : {len(self.episodes_list)}", True, TEXT_FOOTER
        )
        screen.blit(footer, (ui.x(40), footer_y + ui.y(10)))
import pygame
from tools.episode_visualizer.config import (
    ACCENT_CYAN,
    DIVIDER_DARK,
    PANEL_BG,
    PANEL_BORDER,
    PANEL_BORDER_DARK,
    PANEL_HIGHLIGHT,
    TEXT_MUTED,
    TEXT_WHITE,
)


class MetadataPanel:
    """Renders the right panel displaying structured metadata properties."""

    def __init__(self, scene):
        self.scene = scene

    def render(self, screen: pygame.Surface, right_pane_x: int, panel_y: int, right_pane_w: int, panel_h: int):
        ui = self.scene.controller.ui
        state = self.scene.state

        pygame.draw.rect(screen, PANEL_BG, (right_pane_x, panel_y, right_pane_w, panel_h), border_radius=ui.r(8))
        pygame.draw.rect(
            screen, PANEL_BORDER, (right_pane_x, panel_y, right_pane_w, panel_h), width=max(1, ui.r(1)), border_radius=ui.r(8)
        )
        pygame.draw.rect(
            screen,
            PANEL_HIGHLIGHT,
            (right_pane_x + ui.r(2), panel_y + ui.r(2), right_pane_w - ui.r(4), ui.r(3)),
            border_radius=ui.r(2),
        )

        meta_title = self.scene.controller.font.render("METADATA PREVIEW", True, ACCENT_CYAN)
        screen.blit(meta_title, (right_pane_x + ui.w(20), panel_y + ui.h(16)))
        pygame.draw.line(
            screen,
            DIVIDER_DARK,
            (right_pane_x + ui.w(15), panel_y + ui.h(48)),
            (right_pane_x + right_pane_w - ui.w(15), panel_y + ui.h(48)),
            max(1, ui.r(1)),
        )

        if state.selected_metadata:
            curr_y = panel_y + ui.h(64)
            card_gap = ui.h(16)

            for key, val in state.selected_metadata.items():
                if key in ("events", "ticks", "tick_range"):
                    continue

                card_h = ui.h(58)
                if curr_y + card_h > panel_y + panel_h - ui.h(15):
                    break

                card_rect = pygame.Rect(right_pane_x + ui.w(15), curr_y, right_pane_w - ui.w(30), card_h)
                pygame.draw.rect(screen, PANEL_BORDER_DARK, card_rect, border_radius=ui.r(6))

                k_render = self.scene.controller.small_font.render(key.upper(), True, TEXT_MUTED)
                v_render = self.scene.controller.font.render(
                    str(val), True, ACCENT_CYAN if key.lower() == "event_type" else TEXT_WHITE
                )

                screen.blit(k_render, (card_rect.x + ui.w(12), card_rect.y + ui.h(8)))
                screen.blit(v_render, (card_rect.x + ui.w(12), card_rect.y + ui.h(28)))

                curr_y += card_h + card_gap
        else:
            no_meta_str = "No Metadata Structure Discovered" if self.scene.filtered_list else "No Selection Focus Found"
            no_meta = self.scene.controller.small_font.render(no_meta_str, True, TEXT_MUTED)
            screen.blit(
                no_meta,
                no_meta.get_rect(center=(right_pane_x + right_pane_w // 2, panel_y + panel_h // 2)),
            )
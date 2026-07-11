import pygame

from tools.episode_visualizer.config import (
    DIM_BG,
    DIVIDER,
    GUIDE_BG,
    GUIDE_BORDER,
    GUIDE_GREEN,
    GUIDE_ROW_BG,
    TEXT,
    TEXT_MUTED,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    YELLOW,
)


class GuideOverlay:
    def __init__(self, controller):
        self.controller = controller

    def render(self, screen: pygame.Surface):
        self.controller.ui.update(screen)
        ui = self.controller.ui

        # Dim the underlying gameplay scene
        dim_bg = pygame.Surface(
            (ui.w(WINDOW_WIDTH), ui.h(WINDOW_HEIGHT)), pygame.SRCALPHA
        )
        dim_bg.fill(DIM_BG)
        screen.blit(dim_bg, (0, 0))

        panel_width = ui.w(1020)  # Slightly widened for cleaner margins
        panel_height = ui.h(480)

        guide_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)

        # Ensure base background is solid enough to mask underlying text
        base_color = (
            (GUIDE_BG[0], GUIDE_BG[1], GUIDE_BG[2], 245)
            if len(GUIDE_BG) >= 3
            else (GUIDE_BG, 245)
        )
        guide_surface.fill(base_color)

        # Modern UI Touch: Left accent highlight bar
        accent_bar = pygame.Rect(0, 0, ui.w(6), panel_height)
        pygame.draw.rect(
            guide_surface,
            GUIDE_GREEN,
            accent_bar,
            border_top_left_radius=ui.r(12),
            border_bottom_left_radius=ui.r(12),
        )

        # Panel Border
        pygame.draw.rect(
            guide_surface,
            GUIDE_BORDER,
            guide_surface.get_rect(),
            width=max(1, ui.r(2)),
            border_radius=ui.r(12),
        )

        # Header Section
        title = self.controller.big_font.render(
            "DIAGNOSTIC CONTROLS", True, GUIDE_GREEN
        )
        guide_surface.blit(title, (ui.w(40), ui.h(25)))

        close_hint = self.controller.small_font.render(
            "Press F1 to exit guide", True, TEXT_MUTED
        )
        guide_surface.blit(
            close_hint, (panel_width - close_hint.get_width() - ui.w(40), ui.h(32))
        )

        pygame.draw.line(
            guide_surface,
            DIVIDER,
            (ui.w(40), ui.h(70)),
            (panel_width - ui.w(40), ui.h(70)),
            max(1, ui.r(1)),
        )

        # Data Layout Structures
        playback_controls = [
            ("SPACE", "Toggle Play / Pause"),
            ("R", "Restart Episode"),
            ("L", "Toggle Loop Playback"),
            ("← →", "Step Frames"),
            ("↑ ↓", "Adjust Speed"),
            ("1/2/3", "Camera (Follow/Static/Fit)"),
            ("ESC", "Exit to Browser"),
        ]

        overlay_controls = [
            ("H", "Toggle HUD Overlay"),
            ("T", "Toggle Timeline"),
            ("D", "Toggle Direction (Heading)"),
            ("G", "Toggle Metrics Graphs"),
            ("C", "Toggle Confidence View"),
            ("P", "Toggle Path Trail"),
            ("V", "Toggle Raw Telemetry"),
        ]

        # Dynamic center divider placement
        col_w = ui.w(440)
        self._render_column(
            ui,
            guide_surface,
            "SYSTEM PLAYBACK ENGINE",
            playback_controls,
            x_offset=ui.w(45),
            col_width=col_w,
        )

        pygame.draw.line(
            guide_surface,
            DIVIDER,
            (panel_width // 2, ui.h(95)),
            (panel_width // 2, panel_height - ui.h(30)),
            max(1, ui.r(1)),
        )

        self._render_column(
            ui,
            guide_surface,
            "TELEMETRY VISUALIZERS",
            overlay_controls,
            x_offset=panel_width // 2 + ui.w(25),
            col_width=col_w,
        )

        # 5. Composite back to main viewport
        screen.blit(
            guide_surface,
            (
                (ui.w(WINDOW_WIDTH) - panel_width) // 2,
                (ui.h(WINDOW_HEIGHT) - panel_height) // 2,
            ),
        )

    def _render_column(
        self,
        ui,
        surface: pygame.Surface,
        section_title: str,
        items: list,
        x_offset: int,
        col_width: int,
    ):
        """Helper to neatly structure a keybinding column with crisp, premium key-caps."""
        header_surf = self.controller.small_font.render(section_title, True, TEXT_MUTED)
        surface.blit(header_surf, (x_offset, ui.h(95)))

        row_y_start = ui.h(130)
        row_gap = ui.h(44)
        desc_x_align = x_offset + ui.w(115)
        key_box_height = ui.h(26)

        for i, (key, desc) in enumerate(items):
            current_y = row_y_start + (i * row_gap)

            # --- Visual Enhancement: Alternating Row Striping ---
            # Using alternating subtle alpha bands to vastly improve tracking readability
            if i % 2 == 0:
                row_bg_rect = pygame.Rect(
                    x_offset - ui.w(8),
                    current_y - ui.h(6),
                    col_width,
                    row_gap - ui.h(4),
                )
                row_bg_color = (GUIDE_ROW_BG[0], GUIDE_ROW_BG[1], GUIDE_ROW_BG[2], 45)
                pygame.draw.rect(
                    surface, row_bg_color, row_bg_rect, border_radius=ui.r(6)
                )

            # Generate crisp font surfaces
            key_txt = self.controller.font.render(key, True, YELLOW)
            desc_txt = self.controller.font.render(desc, True, TEXT)

            # Calculate precise keycap dimensions
            padding_x = ui.w(16)
            key_box_width = max(ui.w(55), key_txt.get_width() + padding_x)

            # --- Visual Enhancement: Subtle Flat Keycap Shadow ---
            shadow_rect = pygame.Rect(
                x_offset, current_y + ui.r(2), key_box_width, key_box_height
            )
            pygame.draw.rect(
                surface, (5, 5, 8, 200), shadow_rect, border_radius=ui.r(4)
            )

            # Draw crisp primary 'Key Cap' container
            key_rect = pygame.Rect(x_offset, current_y, key_box_width, key_box_height)
            pygame.draw.rect(surface, GUIDE_ROW_BG, key_rect, border_radius=ui.r(4))

            # Keycap inner border glow accent
            pygame.draw.rect(
                surface, DIVIDER, key_rect, width=max(1, ui.r(1)), border_radius=ui.r(4)
            )

            # Center text inside keycap perfectly
            text_x = x_offset + (key_box_width // 2) - (key_txt.get_width() // 2)
            text_y = current_y + (key_box_height // 2) - (key_txt.get_height() // 2)
            surface.blit(key_txt, (text_x, text_y))

            # Render uniform descriptive text tracking line
            desc_y = current_y + (key_box_height // 2) - (desc_txt.get_height() // 2)
            surface.blit(desc_txt, (desc_x_align, desc_y))

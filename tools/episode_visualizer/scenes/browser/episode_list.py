# tools/episode_visualizer/scenes/browser/episode_list.py

import pygame
from tools.episode_visualizer.config import (
    ACCENT_BLUE,
    ACCENT_CYAN,
    ACCENT_CYAN_DIM,
    BACKGROUND,
    PANEL_BORDER,
    PANEL_BORDER_DARK,
    ROW_ALT_BG,
    SELECT_ARROW,
    SELECT_BAR,
    SELECT_GLOW,
    TEXT_DIM,
    TEXT_MUTED,
    TEXT_WHITE,
)


class EpisodeListPanel:
    """Handles rendering the central list (Runs or Episodes) and the search bar."""

    def __init__(self, scene):
        self.scene = scene

    def get_search_suggestion(self) -> str:
        state = self.scene.state
        if not state.search_active:
            return "Ctrl+F to Filter..."
        if not state.search_query:
            return "Type keyword strings to filter entries..."
        return ""

    def render(
        self,
        screen: pygame.Surface,
        panel_x: int,
        panel_y: int,
        left_pane_w: int,
        panel_h: int,
    ):
        ui = self.scene.controller.ui
        state = self.scene.state

        # Search Bar
        search_bar_h = ui.h(40)
        search_rect = pygame.Rect(
            panel_x + ui.w(12), panel_y + ui.h(12), left_pane_w - ui.w(24), search_bar_h
        )
        search_border_color = ACCENT_CYAN if state.search_active else PANEL_BORDER_DARK

        pygame.draw.rect(screen, BACKGROUND, search_rect, border_radius=ui.r(6))
        pygame.draw.rect(
            screen,
            search_border_color,
            search_rect,
            width=max(1, ui.r(1)),
            border_radius=ui.r(6),
        )

        prefix_str = "FILTER: " if state.search_query else ""
        prefix_color = ACCENT_CYAN if state.search_active else TEXT_MUTED
        prefix_render = self.scene.controller.font.render(
            prefix_str, True, prefix_color
        )
        screen.blit(
            prefix_render,
            (
                search_rect.x + ui.w(10),
                search_rect.y
                + (search_rect.height // 2 - prefix_render.get_height() // 2),
            ),
        )

        text_offset = ui.w(10) + prefix_render.get_width()
        if state.search_query:
            query_render = self.scene.controller.font.render(
                state.search_query, True, TEXT_WHITE
            )
            screen.blit(
                query_render,
                (
                    search_rect.x + text_offset,
                    search_rect.y
                    + (search_rect.height // 2 - query_render.get_height() // 2),
                ),
            )
            text_offset += query_render.get_width()

        suggestion = self.get_search_suggestion()
        if suggestion and not state.search_query:
            hint_render = self.scene.controller.font.render(
                suggestion, True, TEXT_MUTED
            )
            screen.blit(
                hint_render,
                (
                    search_rect.x + text_offset,
                    search_rect.y
                    + (search_rect.height // 2 - hint_render.get_height() // 2),
                ),
            )

        list_start_y = search_rect.bottom + ui.h(10)

        # Header Bar when inside an episode list (Shows Active Run Name)
        if state.current_view == "EPISODES":
            header_rect = pygame.Rect(
                panel_x + ui.w(12), list_start_y, left_pane_w - ui.w(24), ui.h(32)
            )
            pygame.draw.rect(
                screen, PANEL_BORDER_DARK, header_rect, border_radius=ui.r(6)
            )

            run_lbl = self.scene.controller.small_font.render(
                f"RUN: {state.selected_run_name.upper()}  (Press BACKSPACE / ESC to return to Runs)",
                True,
                ACCENT_CYAN,
            )
            screen.blit(
                run_lbl,
                (
                    header_rect.x + ui.w(10),
                    header_rect.y
                    + (header_rect.height // 2 - run_lbl.get_height() // 2),
                ),
            )
            list_start_y = header_rect.bottom + ui.h(8)

        list_usable_h = panel_h - (list_start_y - panel_y) - ui.h(12)
        row_height = ui.h(42)
        visible_rows = max(1, list_usable_h // row_height)

        filtered_list = self.scene.filtered_list
        start_idx = 0
        if len(filtered_list) > visible_rows:
            start_idx = max(
                0,
                min(
                    state.selected_idx - visible_rows // 2,
                    len(filtered_list) - visible_rows,
                ),
            )
        end_idx = min(start_idx + visible_rows, len(filtered_list))

        for render_slot, idx in enumerate(range(start_idx, end_idx)):
            item_path = filtered_list[idx]
            y_pos = list_start_y + render_slot * row_height
            selected = idx == state.selected_idx
            row_rect = pygame.Rect(
                panel_x + ui.w(12), y_pos, left_pane_w - ui.w(40), row_height - ui.h(4)
            )

            if idx % 2 == 0 and not selected:
                pygame.draw.rect(screen, ROW_ALT_BG, row_rect, border_radius=ui.r(6))

            if selected:
                pygame.draw.rect(screen, SELECT_GLOW, row_rect, border_radius=ui.r(6))
                pygame.draw.rect(
                    screen,
                    SELECT_BAR,
                    (row_rect.x, row_rect.y, ui.w(4), row_rect.height),
                    border_radius=ui.r(2),
                )
                arrow_center_y = row_rect.y + row_rect.height // 2
                pygame.draw.polygon(
                    screen,
                    SELECT_ARROW,
                    [
                        (panel_x + ui.w(22), arrow_center_y),
                        (panel_x + ui.w(30), arrow_center_y - ui.h(5)),
                        (panel_x + ui.w(30), arrow_center_y + ui.h(5)),
                    ],
                )
                text_color = TEXT_WHITE
                text_padding_offset = ui.w(8)
            else:
                text_color = TEXT_DIM
                text_padding_offset = 0

            index_text = self.scene.controller.font.render(
                f"{idx + 1:02d}.", True, ACCENT_BLUE
            )
            screen.blit(
                index_text,
                (
                    panel_x + ui.w(40) + text_padding_offset,
                    y_pos + (row_rect.height // 2) - (index_text.get_height() // 2),
                ),
            )

            max_chars = int((row_rect.width - ui.w(100)) // ui.w(13))
            item_name = item_path.name
            display_name = (
                item_name
                if len(item_name) <= max_chars
                else f"{item_name[:max_chars-3]}..."
            )

            # Format display label (indicate directory/run folder vs episode)
            prefix_tag = "[RUN] " if state.current_view == "RUNS" else ""
            name_text = self.scene.controller.font.render(
                f"{prefix_tag}{display_name}", True, text_color
            )
            screen.blit(
                name_text,
                (
                    panel_x + ui.w(85) + text_padding_offset,
                    y_pos + (row_rect.height // 2) - (name_text.get_height() // 2),
                ),
            )

        if len(filtered_list) > visible_rows:
            sb_track_x = panel_x + left_pane_w - ui.w(16)
            sb_track_y = list_start_y
            sb_track_h = list_usable_h
            sb_track_w = ui.w(6)

            pygame.draw.rect(
                screen,
                PANEL_BORDER_DARK,
                (sb_track_x, sb_track_y, sb_track_w, sb_track_h),
                border_radius=ui.r(3),
            )
            thumb_h = max(
                ui.h(20), int(sb_track_h * (visible_rows / len(filtered_list)))
            )
            scroll_pct = start_idx / (len(filtered_list) - visible_rows)
            thumb_y = sb_track_y + int(scroll_pct * (sb_track_h - thumb_h))
            pygame.draw.rect(
                screen,
                ACCENT_CYAN_DIM,
                (sb_track_x, thumb_y, sb_track_w, thumb_h),
                border_radius=ui.r(3),
            )

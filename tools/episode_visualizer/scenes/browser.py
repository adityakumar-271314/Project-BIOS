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
    TEXT,
    TEXT_DIM,
    TEXT_FOOTER,
    TEXT_MUTED,
    TEXT_WHITE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from tools.episode_visualizer.replay_loader import (
    load_from_storage,
    load_metadata_from_storage,
)
from tools.episode_visualizer.scenes.base import Scene

class BrowserScene(Scene):
    def __init__(self, controller):
        super().__init__(controller)
        self.browser_util = EpisodeBrowser()
        self.episodes_list = []
        self.cached_metadata = {}
        self.filtered_list = []
        self.selected_idx = 0
        self.selected_metadata = {}

        # Search / Filter Panel States
        self.search_query = ""
        self.search_active = False
        self.show_filters = True
        self.dragging_slider = (
            None  # Track which slider/handle: 'sig', 'tick_start', 'tick_end'
        )
        self.hovered_item = None
        # Filter Options
        self.event_types = [
            "damage_spike",
            "food_recovery",
            "hazard_encounter",
            "danger_state",
            "starvation_state",
            "high_significance",
        ]
        self.active_event_filter = None
        self.min_peak_significance = 0
        self.episode_id_filter = ""

        # Dual-Handle Tick Boundaries
        self.max_repository_ticks = 2000  # Dynamic fallback baseline upper limit
        self.tick_start = 0
        self.tick_end = self.max_repository_ticks

        self.refresh_browser_list()

    def on_enter(self, **kwargs):
        self.refresh_browser_list()

    def refresh_browser_list(self):
        try:
            self.episodes_list = self.browser_util.list()
            self.cached_metadata.clear()
            lowest_tick = float("inf")
            highest_tick = 0

            for path in self.episodes_list:
                meta = load_metadata_from_storage(path) or {}
                self.cached_metadata[str(path)] = meta

                # Extract specific episode bounds (fallback to 0 and dynamic ticks if missing)
                ep_start = int(meta.get("start_tick", 0))
                ep_end = int(
                    meta.get("ticks", meta.get("frames", meta.get("end_tick", 2000)))
                )
                if isinstance(ep_end, list) and ep_end:
                    ep_end = max(ep_end)

                # Cache calculated bounds back into metadata for quick lookup inside filters
                meta["_calculated_start"] = ep_start
                meta["_calculated_end"] = ep_end

                if ep_start < lowest_tick:
                    lowest_tick = ep_start
                if ep_end > highest_tick:
                    highest_tick = ep_end

            self.min_repository_ticks = (
                lowest_tick if lowest_tick != float("inf") else 0
            )
            self.max_repository_ticks = max(highest_tick, 2000)

            # Initialize slider positions to outer bounds of the entire repository
            self.tick_start = self.min_repository_ticks
            self.tick_end = self.max_repository_ticks
            self.apply_filters()
        except FileNotFoundError:
            self.episodes_list = []
            self.filtered_list = []
            self.selected_idx = 0
            self.selected_metadata = {}
        except Exception as e:
            self.controller.trigger_error(f"Failed listing target paths: {e}")

    def apply_filters(self):
        results = list(self.episodes_list)

        # 1. Text Search Filter
        if self.search_query:
            q = self.search_query.lower()
            results = [p for p in results if q in p.name.lower()]

        # 2. Event Type Chip Filter
        if self.active_event_filter:
            target_ev = self.active_event_filter.lower().strip()

            def matches_event(ep):
                meta = self.cached_metadata.get(str(ep), {})
                event_type = meta.get("event_type", "")
                if isinstance(event_type, dict):
                    event_type = event_type.get("type", event_type)
                ev_str = str(event_type).lower().strip()
                return target_ev == ev_str or target_ev in ev_str or ev_str in target_ev

            results = [p for p in results if matches_event(p)]

        # 3. Significance Slider Filter
        if self.min_peak_significance > 0:

            def has_peak(ep):
                meta = self.cached_metadata.get(str(ep), {})
                val = meta.get("peak_significance", meta.get("significance", 0))
                return int(val) >= self.min_peak_significance

            results = [p for p in results if has_peak(p)]

        # 4. Episode ID Side-Filter
        if self.episode_id_filter:
            q = self.episode_id_filter.lower()
            results = [p for p in results if q in str(p.name).lower()]

        # 5. Tick Range Filter (Evaluated cleanly against invariant global boundaries)
        def in_tick_range(ep):
            meta = self.cached_metadata.get(str(ep), {})
            ep_start = meta.get("_calculated_start", 0)
            ep_end = meta.get("_calculated_end", 2000)
            return self.tick_start <= ep_start and ep_end <= self.tick_end

        self.filtered_list = [p for p in results if in_tick_range(p)]
        self.selected_idx = max(0, min(self.selected_idx, len(self.filtered_list) - 1))
        self.update_preview()

    def update_preview(self):
        if self.filtered_list and 0 <= self.selected_idx < len(self.filtered_list):
            target_folder = self.filtered_list[self.selected_idx]
            self.selected_metadata = self.cached_metadata.get(str(target_folder), {})
        else:
            self.selected_metadata = {}

    def _get_search_suggestion(self):
        if not self.search_active:
            return "Ctrl+F to Filter..."
        if not self.search_query:
            return "Type keyword strings to filter entries..."
        return ""

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self._handle_mouse_down(event.pos)
        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging_slider = None
            return True
        if event.type == pygame.MOUSEMOTION:
            self.hovered_item = self._get_hovered(event.pos)
            if self.dragging_slider:
                self._update_slider(event.pos)
                return True
        if event.type != pygame.KEYDOWN:
            return False
        if event.key == pygame.K_f and (pygame.key.get_mods() & pygame.KMOD_CTRL):
            self.search_active = not self.search_active
            return True
        if self.search_active and event.key not in (
            pygame.K_ESCAPE,
            pygame.K_RETURN,
            pygame.K_UP,
            pygame.K_DOWN,
        ):
            if event.key == pygame.K_BACKSPACE:
                self.search_query = self.search_query[:-1]
            elif event.unicode.isprintable():
                self.search_query += event.unicode
            self.apply_filters()
            return True
        original_idx = self.selected_idx
        if event.key == pygame.K_UP:
            self.selected_idx = max(0, self.selected_idx - 1)
        elif event.key == pygame.K_DOWN:
            self.selected_idx = min(len(self.filtered_list) - 1, self.selected_idx + 1)
        elif event.key == pygame.K_ESCAPE:
            if self.search_active:
                self.search_active = False
            else:
                self.controller.running = False
            return True
        elif event.key == pygame.K_RETURN and self.filtered_list:
            if self.search_active:
                self.search_active = False
                return True
            try:
                target_folder = self.filtered_list[self.selected_idx]
                session = load_from_storage(target_folder)
                self.controller.switch_to_scene("PLAYBACK", session=session)
            except Exception as e:
                self.controller.trigger_error(f"Reconstruction Halt Constraint: {e}")
            return True
        if self.selected_idx != original_idx:
            self.update_preview()
        return True

    def _update_slider(self, pos):
        ui = self.controller.ui
        tick_range = self.max_repository_ticks - self.min_repository_ticks
        if self.dragging_slider == "sig":
            slider_rect = self._get_slider_rect()
            rel_x = max(0.0, min(1.0, (pos[0] - slider_rect.x) / slider_rect.width))
            self.min_peak_significance = int(rel_x * 100)
        elif self.dragging_slider in ("tick_start", "tick_end"):
            tick_rect = self._get_tick_slider_rect()
            rel_x = max(0.0, min(1.0, (pos[0] - tick_rect.x) / tick_rect.width))
            val = self.min_repository_ticks + int(rel_x * tick_range)
            if self.dragging_slider == "tick_start":
                self.tick_start = max(
                    self.min_repository_ticks, min(val, self.tick_end - 1)
                )
            else:
                self.tick_end = max(
                    self.tick_start + 1, min(val, self.max_repository_ticks)
                )
        self.apply_filters()

    def _handle_mouse_down(self, pos):
        ui = self.controller.ui

        # Global Side Panel Toggle Check
        if ui.x(40) <= pos[0] <= ui.x(200) and ui.y(70) <= pos[1] <= ui.y(105):
            self.show_filters = not self.show_filters
            return True

        # If filters aren't being displayed, do not register clicks on panel children
        if not self.show_filters:
            return False

        # Check Reset Button immediately (prevents early returns blocking it)
        if self._is_in_reset_button(pos):
            self.reset_all_filters()
            return True

        # Check Event Category Selection Chips
        for i, et in enumerate(self.event_types):
            rect = self._get_chip_rect(i)
            if rect.collidepoint(pos):
                self.active_event_filter = (
                    None if self.active_event_filter == et else et
                )
                self.apply_filters()
                return True

        # Check Significance Slider Area
        if self._get_slider_rect().collidepoint(pos):
            self.dragging_slider = "sig"
            self._update_slider(pos)
            return True

        # 5. Check Dual-Handle Tick Slider Area
        tick_rect = self._get_tick_slider_rect()
        if tick_rect.inflate(0, 10).collidepoint(pos):
            rel_x = (pos[0] - tick_rect.x) / tick_rect.width
            tick_range = self.max_repository_ticks - self.min_repository_ticks
            val = self.min_repository_ticks + int(rel_x * tick_range)

            if abs(val - self.tick_start) < abs(val - self.tick_end):
                self.dragging_slider = "tick_start"
            else:
                self.dragging_slider = "tick_end"
            self._update_slider(pos)
            return True

        return False

    def reset_all_filters(self):
        self.active_event_filter = None
        self.min_peak_significance = 0
        self.episode_id_filter = ""
        self.tick_start = self.min_repository_ticks
        self.tick_end = self.max_repository_ticks
        self.search_query = ""
        self.apply_filters()

    def _get_hovered(self, pos):
        return None

    def _get_chip_rect(self, i):
        ui = self.controller.ui
        return pygame.Rect(ui.x(45), ui.y(160 + i * 36), ui.w(245), ui.h(28))

    def _get_slider_rect(self):
        ui = self.controller.ui
        return pygame.Rect(ui.x(45), ui.y(415), ui.w(245), ui.h(8))

    def _get_tick_slider_rect(self):
        ui = self.controller.ui
        return pygame.Rect(ui.x(45), ui.y(475), ui.w(245), ui.h(8))

    def _is_in_reset_button(self, pos):
        ui = self.controller.ui
        panel_h = ui.h(WINDOW_HEIGHT) - ui.y(165)
        panel = pygame.Rect(ui.x(35), ui.y(110), ui.w(265), panel_h)
        reset_rect = pygame.Rect(
            panel.x + ui.w(12),
            panel.y + panel.height - ui.h(46),
            panel.width - ui.w(24),
            ui.h(34),
        )
        return reset_rect.collidepoint(pos)

    def _render_filter_panel(self, screen, ui):
        panel_h = ui.h(WINDOW_HEIGHT) - ui.y(165)
        panel = pygame.Rect(ui.x(35), ui.y(110), ui.w(265), panel_h)
        pygame.draw.rect(screen, PANEL_BG, panel, border_radius=ui.r(8))
        pygame.draw.rect(
            screen, PANEL_BORDER, panel, width=max(1, ui.r(1)), border_radius=ui.r(8)
        )

        y = panel.y + ui.h(14)
        screen.blit(
            self.controller.font.render("EVENT CATEGORIES", True, ACCENT_CYAN),
            (panel.x + ui.w(12), y),
        )

        for i, et in enumerate(self.event_types):
            rect = self._get_chip_rect(i)
            is_active = self.active_event_filter == et
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

            txt = self.controller.small_font.render(
                et.replace("_", " ").upper(), True, color
            )
            screen.blit(
                txt,
                (
                    rect.x + ui.w(10),
                    rect.y + (rect.height // 2 - txt.get_height() // 2),
                ),
            )

        # 1. Significance Slider
        slider_rect = self._get_slider_rect()
        y_slider_lbl = slider_rect.y - ui.h(22)
        screen.blit(
            self.controller.small_font.render(
                f"MIN SIGNIFICANCE: {self.min_peak_significance}/100", True, TEXT
            ),
            (panel.x + ui.w(12), y_slider_lbl),
        )

        pygame.draw.rect(screen, PANEL_BORDER_DARK, slider_rect, border_radius=ui.r(4))
        fill_w = int(slider_rect.width * (self.min_peak_significance / 100))
        if fill_w > 0:
            pygame.draw.rect(
                screen,
                ACCENT_CYAN,
                (slider_rect.x, slider_rect.y, fill_w, slider_rect.height),
                border_radius=ui.r(4),
            )

        # 2. Dual-Handle Dynamic Range Slider
        tick_rect = self._get_tick_slider_rect()
        y_tick_lbl = tick_rect.y - ui.h(22)
        screen.blit(
            self.controller.small_font.render(
                f"TICK RANGE: {self.tick_start} - {self.tick_end}", True, TEXT
            ),
            (panel.x + ui.w(12), y_tick_lbl),
        )

        pygame.draw.rect(screen, PANEL_BORDER_DARK, tick_rect, border_radius=ui.r(4))

        tick_range = self.max_repository_ticks - self.min_repository_ticks
        denom = tick_range if tick_range > 0 else 1
        start_x = tick_rect.x + int(
            tick_rect.width * ((self.tick_start - self.min_repository_ticks) / denom)
        )
        end_x = tick_rect.x + int(
            tick_rect.width * ((self.tick_end - self.min_repository_ticks) / denom)
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

        # Anchored Bottom Action Button
        reset_rect = pygame.Rect(
            panel.x + ui.w(12),
            panel.y + panel.height - ui.h(46),
            panel.width - ui.w(24),
            ui.h(34),
        )
        pygame.draw.rect(screen, ERROR_RED, reset_rect, border_radius=ui.r(6))
        reset_txt = self.controller.small_font.render(
            "RESET ALL FILTERS", True, TEXT_WHITE
        )
        screen.blit(reset_txt, reset_txt.get_rect(center=reset_rect.center))

    def render(self, screen: pygame.Surface):
        screen.fill(BACKGROUND)
        self.controller.ui.update(screen)
        ui = self.controller.ui

        if not self.episodes_list:
            title = self.controller.big_font.render("EMPTY REPOSITORY", True, ERROR_RED)
            msg = self.controller.font.render(
                "No playable episodes were discovered.", True, TEXT_MUTED
            )
            hint = self.controller.font.render("Press F1 for Help", True, TEXT_DIM)
            screen.blit(
                title,
                title.get_rect(
                    center=(
                        ui.w(WINDOW_WIDTH) // 2,
                        ui.h(WINDOW_HEIGHT) // 2 - ui.h(50),
                    )
                ),
            )
            screen.blit(
                msg,
                msg.get_rect(
                    center=(ui.w(WINDOW_WIDTH) // 2, ui.h(WINDOW_HEIGHT) // 2)
                ),
            )
            screen.blit(
                hint,
                hint.get_rect(
                    center=(
                        ui.w(WINDOW_WIDTH) // 2,
                        ui.h(WINDOW_HEIGHT) // 2 + ui.h(45),
                    )
                ),
            )
            return
        title = self.controller.big_font.render(
            "SYSTEM EPISODE BROWSER", True, ACCENT_CYAN
        )
        screen.blit(title, (ui.x(40), ui.y(25)))
        toggle_rect = pygame.Rect(ui.x(40), ui.y(70), ui.w(135), ui.h(32))
        pygame.draw.rect(screen, PANEL_BG, toggle_rect, border_radius=ui.r(6))
        pygame.draw.rect(
            screen,
            PANEL_BORDER,
            toggle_rect,
            width=max(1, ui.r(1)),
            border_radius=ui.r(6),
        )
        toggle_text = self.controller.small_font.render(
            f"SIDE PANEL {'v' if self.show_filters else '>'}", True, ACCENT_CYAN
        )
        screen.blit(toggle_text, toggle_text.get_rect(center=toggle_rect.center))

        # Modern, structured shortcut tags
        shortcuts = [
            ("↑↓", "Navigate"),
            ("ENTER", "Load Episode"),
            ("Ctrl+F", "Filter Search"),
            ("F1", "Open Guide"),
            ("ESC", "Exit"),
        ]

        current_x = toggle_rect.right + ui.w(20)
        text_y_center = toggle_rect.y + toggle_rect.height // 2
        for key, action in shortcuts:
            # Render Key Indicator (Highlighted)
            key_render = self.controller.small_font.render(
                f"[{key}]", True, ACCENT_BLUE
            )
            screen.blit(
                key_render, (current_x, text_y_center - key_render.get_height() // 2)
            )
            current_x += key_render.get_width() + ui.w(4)

            # Render Action Label (Muted)
            action_render = self.controller.small_font.render(action, True, TEXT_MUTED)
            screen.blit(
                action_render,
                (current_x, text_y_center - action_render.get_height() // 2),
            )
            current_x += action_render.get_width() + ui.w(16)  # Space between pairs

        pygame.draw.line(
            screen,
            ACCENT_CYAN_DIM,
            (ui.x(40), ui.y(64)),
            (ui.w(WINDOW_WIDTH) - ui.x(40), ui.y(64)),
            max(1, ui.r(1)),
        )
        panel_x = ui.x(320) if self.show_filters else ui.x(35)
        panel_y = ui.y(110)
        panel_w = ui.w(WINDOW_WIDTH) - panel_x - ui.x(35)
        panel_h = ui.h(WINDOW_HEIGHT) - ui.y(165)
        left_pane_w = int(panel_w * 0.60)
        right_pane_x = panel_x + left_pane_w + ui.w(15)
        right_pane_w = panel_w - left_pane_w - ui.w(15)
        if self.show_filters:
            self._render_filter_panel(screen, ui)
        pygame.draw.rect(
            screen,
            PANEL_BG,
            (panel_x, panel_y, left_pane_w, panel_h),
            border_radius=ui.r(8),
        )
        pygame.draw.rect(
            screen,
            PANEL_BORDER,
            (panel_x, panel_y, left_pane_w, panel_h),
            width=max(1, ui.r(1)),
            border_radius=ui.r(8),
        )
        search_bar_h = ui.h(40)
        search_rect = pygame.Rect(
            panel_x + ui.w(12), panel_y + ui.h(12), left_pane_w - ui.w(24), search_bar_h
        )
        search_border_color = ACCENT_CYAN if self.search_active else PANEL_BORDER_DARK

        pygame.draw.rect(screen, BACKGROUND, search_rect, border_radius=ui.r(6))
        pygame.draw.rect(
            screen,
            search_border_color,
            search_rect,
            width=max(1, ui.r(1)),
            border_radius=ui.r(6),
        )

        prefix_str = "FILTER: " if self.search_query else ""
        prefix_color = ACCENT_CYAN if self.search_active else TEXT_MUTED
        prefix_render = self.controller.font.render(prefix_str, True, prefix_color)
        screen.blit(
            prefix_render,
            (
                search_rect.x + ui.w(10),
                search_rect.y
                + (search_rect.height // 2 - prefix_render.get_height() // 2),
            ),
        )

        text_offset = ui.w(10) + prefix_render.get_width()
        if self.search_query:
            query_render = self.controller.font.render(
                self.search_query, True, TEXT_WHITE
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
        suggestion = self._get_search_suggestion()
        if suggestion and not self.search_query:
            hint_render = self.controller.font.render(suggestion, True, TEXT_MUTED)
            screen.blit(
                hint_render,
                (
                    search_rect.x + text_offset,
                    search_rect.y
                    + (search_rect.height // 2 - hint_render.get_height() // 2),
                ),
            )
        list_start_y = search_rect.bottom + ui.h(10)
        list_usable_h = panel_h - (list_start_y - panel_y) - ui.h(12)

        row_height = ui.h(42)
        visible_rows = max(1, list_usable_h // row_height)

        start_idx = 0
        if len(self.filtered_list) > visible_rows:
            start_idx = max(
                0,
                min(
                    self.selected_idx - visible_rows // 2,
                    len(self.filtered_list) - visible_rows,
                ),
            )
        end_idx = min(start_idx + visible_rows, len(self.filtered_list))
        for render_slot, idx in enumerate(range(start_idx, end_idx)):
            path = self.filtered_list[idx]
            y_pos = list_start_y + render_slot * row_height
            selected = idx == self.selected_idx
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
            index_text = self.controller.font.render(
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
            display_name = (
                path.name
                if len(path.name) <= max_chars
                else f"{path.name[:max_chars-3]}..."
            )

            name_text = self.controller.font.render(display_name, True, text_color)
            screen.blit(
                name_text,
                (
                    panel_x + ui.w(85) + text_padding_offset,
                    y_pos + (row_rect.height // 2) - (name_text.get_height() // 2),
                ),
            )
        if len(self.filtered_list) > visible_rows:
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
                ui.h(20), int(sb_track_h * (visible_rows / len(self.filtered_list)))
            )
            scroll_pct = start_idx / (len(self.filtered_list) - visible_rows)
            thumb_y = sb_track_y + int(scroll_pct * (sb_track_h - thumb_h))
            pygame.draw.rect(
                screen,
                ACCENT_CYAN_DIM,
                (sb_track_x, thumb_y, sb_track_w, thumb_h),
                border_radius=ui.r(3),
            )
        # Spacious & Structural Metadata Card Layout Changes
        pygame.draw.rect(
            screen,
            PANEL_BG,
            (right_pane_x, panel_y, right_pane_w, panel_h),
            border_radius=ui.r(8),
        )
        pygame.draw.rect(
            screen,
            PANEL_BORDER,
            (right_pane_x, panel_y, right_pane_w, panel_h),
            width=max(1, ui.r(1)),
            border_radius=ui.r(8),
        )
        pygame.draw.rect(
            screen,
            PANEL_HIGHLIGHT,
            (
                right_pane_x + ui.r(2),
                panel_y + ui.r(2),
                right_pane_w - ui.r(4),
                ui.r(3),
            ),
            border_radius=ui.r(2),
        )

        meta_title = self.controller.font.render("METADATA PREVIEW", True, ACCENT_CYAN)
        screen.blit(meta_title, (right_pane_x + ui.w(20), panel_y + ui.h(16)))
        pygame.draw.line(
            screen,
            DIVIDER_DARK,
            (right_pane_x + ui.w(15), panel_y + ui.h(48)),
            (right_pane_x + right_pane_w - ui.w(15), panel_y + ui.h(48)),
            max(1, ui.r(1)),
        )
        if self.selected_metadata:
            curr_y = panel_y + ui.h(64)
            card_gap = ui.h(16)  # Deep spacious layout gap between cards

            for key, val in self.selected_metadata.items():
                if key in ("events", "ticks", "tick_range"):
                    continue

                card_h = ui.h(58)
                if curr_y + card_h > panel_y + panel_h - ui.h(15):
                    break

                # Render structured background cards for distinct property field separation
                card_rect = pygame.Rect(
                    right_pane_x + ui.w(15), curr_y, right_pane_w - ui.w(30), card_h
                )
                pygame.draw.rect(
                    screen, PANEL_BORDER_DARK, card_rect, border_radius=ui.r(6)
                )

                k_render = self.controller.small_font.render(
                    key.upper(), True, TEXT_MUTED
                )
                v_render = self.controller.font.render(
                    str(val),
                    True,
                    ACCENT_CYAN if key.lower() == "event_type" else TEXT_WHITE,
                )

                screen.blit(k_render, (card_rect.x + ui.w(12), card_rect.y + ui.h(8)))
                screen.blit(v_render, (card_rect.x + ui.w(12), card_rect.y + ui.h(28)))

                curr_y += card_h + card_gap
        else:
            no_meta_str = (
                "No Metadata Structure Discovered"
                if self.filtered_list
                else "No Selection Focus Found"
            )
            no_meta = self.controller.small_font.render(no_meta_str, True, TEXT_MUTED)
            screen.blit(
                no_meta,
                no_meta.get_rect(
                    center=(right_pane_x + right_pane_w // 2, panel_y + panel_h // 2)
                ),
            )
        footer_y = ui.h(WINDOW_HEIGHT) - ui.y(42)
        pygame.draw.line(
            screen,
            DIVIDER_DARK,
            (ui.x(35), footer_y),
            (ui.w(WINDOW_WIDTH) - ui.x(35), footer_y),
            max(1, ui.r(1)),
        )
        summary_tags = []
        if self.active_event_filter:
            summary_tags.append(f"CATEGORY:{self.active_event_filter.upper()}")
        if self.min_peak_significance > 0:
            summary_tags.append(f"SIG≥{self.min_peak_significance}")
        if self.tick_start > 0 or self.tick_end < self.max_repository_ticks:
            summary_tags.append(f"TICKS:{self.tick_start}-{self.tick_end}")

        repo_count = f"REPLAYS FOUND : {len(self.filtered_list)}"
        if self.search_query or summary_tags:
            repo_count += f" (FILTER MATCHED : {len(self.filtered_list)} / {len(self.episodes_list)})"
        if summary_tags:
            repo_count += " [" + " | ".join(summary_tags) + "]"

        footer = self.controller.small_font.render(repo_count, True, TEXT_FOOTER)
        screen.blit(footer, (ui.x(40), footer_y + ui.y(10)))

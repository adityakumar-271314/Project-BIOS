# tools/episode_visualizer/scenes/browser/scene.py

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
    TEXT_FOOTER,
    TEXT_MUTED,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from tools.episode_visualizer.replay_loader import (
    load_from_storage,
    load_metadata_from_storage,
)
from tools.episode_visualizer.scenes.base import Scene
from tools.episode_visualizer.scenes.browser.episode_list import EpisodeListPanel
from tools.episode_visualizer.scenes.browser.filter_panel import FilterPanel
from tools.episode_visualizer.scenes.browser.metadata_panel import MetadataPanel
from tools.episode_visualizer.scenes.browser.state import BrowserState


class BrowserScene(Scene):
    """Main orchestrator scene for browsing runs and episodes."""

    def __init__(self, controller):
        super().__init__(controller)
        self.browser_util = EpisodeBrowser()
        self.state = BrowserState()

        self.runs_list = []
        self.episodes_list = []
        self.cached_metadata = {}
        self.filtered_list = []

        self.filter_panel = FilterPanel(self)
        self.metadata_panel = MetadataPanel(self)
        self.episode_list_panel = EpisodeListPanel(self)

        self.refresh_browser_list()

    def on_enter(self, **kwargs):
        self.refresh_browser_list()

    def refresh_browser_list(self):
        try:
            if self.state.current_view == "RUNS":
                self.runs_list = self.browser_util.list_runs()
                self.apply_filters()
            else:
                self.episodes_list = self.browser_util.list_episodes(run_id=self.state.selected_run_name)
                self.cached_metadata.clear()
                lowest_tick = float("inf")
                highest_tick = 0

                for path in self.episodes_list:
                    meta = load_metadata_from_storage(path) or {}
                    self.cached_metadata[str(path)] = meta

                    ep_start = int(meta.get("start_tick", 0))
                    ep_end = int(meta.get("ticks", meta.get("frames", meta.get("end_tick", 2000))))
                    if isinstance(ep_end, list) and ep_end:
                        ep_end = max(ep_end)

                    meta["_calculated_start"] = ep_start
                    meta["_calculated_end"] = ep_end

                    if ep_start < lowest_tick:
                        lowest_tick = ep_start
                    if ep_end > highest_tick:
                        highest_tick = ep_end

                self.state.min_repository_ticks = lowest_tick if lowest_tick != float("inf") else 0
                self.state.max_repository_ticks = max(highest_tick, 2000)

                self.state.tick_start = self.state.min_repository_ticks
                self.state.tick_end = self.state.max_repository_ticks
                self.apply_filters()
        except FileNotFoundError:
            self.runs_list = []
            self.episodes_list = []
            self.filtered_list = []
            self.state.selected_idx = 0
            self.state.selected_metadata = {}
        except Exception as e:
            self.controller.trigger_error(f"Failed listing target paths: {e}")

    def apply_filters(self):
        if self.state.current_view == "RUNS":
            results = list(self.runs_list)
            if self.state.search_query:
                q = self.state.search_query.lower()
                results = [p for p in results if q in p.name.lower()]
            self.filtered_list = results
        else:
            results = list(self.episodes_list)

            if self.state.search_query:
                q = self.state.search_query.lower()
                results = [p for p in results if q in p.name.lower()]

            if self.state.active_event_filter:
                target_ev = self.state.active_event_filter.lower().strip()

                def matches_event(ep):
                    meta = self.cached_metadata.get(str(ep), {})
                    event_type = meta.get("event_type", "")
                    if isinstance(event_type, dict):
                        event_type = event_type.get("type", event_type)
                    ev_str = str(event_type).lower().strip()
                    return target_ev == ev_str or target_ev in ev_str or ev_str in target_ev

                results = [p for p in results if matches_event(p)]

            if self.state.min_peak_significance > 0:

                def has_peak(ep):
                    meta = self.cached_metadata.get(str(ep), {})
                    val = meta.get("peak_significance", meta.get("significance", 0))
                    return int(val) >= self.state.min_peak_significance

                results = [p for p in results if has_peak(p)]

            def in_tick_range(ep):
                meta = self.cached_metadata.get(str(ep), {})
                ep_start = meta.get("_calculated_start", 0)
                ep_end = meta.get("_calculated_end", 2000)
                return self.state.tick_start <= ep_start and ep_end <= self.state.tick_end

            self.filtered_list = [p for p in results if in_tick_range(p)]

        self.state.selected_idx = max(0, min(self.state.selected_idx, len(self.filtered_list) - 1))
        self.update_preview()


    def update_preview(self):
        if self.filtered_list and 0 <= self.state.selected_idx < len(self.filtered_list):
            target_folder = self.filtered_list[self.state.selected_idx]
            if self.state.current_view == "RUNS":
                episodes_in_run = self.browser_util.list_episodes(run_id=target_folder.name)
                
                # Check for run-level manifest metadata if present
                manifest_path = target_folder / "episodes" / "manifest.json"
                manifest_data = {}
                if manifest_path.exists():
                    try:
                        import json
                        with open(manifest_path, "r") as f:
                            manifest_data = json.load(f)
                    except Exception:
                        pass

                self.state.selected_metadata = {
                    "run_id": target_folder.name,
                    "episodes_count": len(episodes_in_run),
                    "path": str(target_folder),
                    **manifest_data,
                }
            else:
                self.state.selected_metadata = self.cached_metadata.get(str(target_folder), {})
        else:
            self.state.selected_metadata = {}

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self._handle_mouse_down(event.pos)
        if event.type == pygame.MOUSEBUTTONUP:
            self.state.dragging_slider = None
            return True
        if event.type == pygame.MOUSEMOTION:
            if self.state.dragging_slider:
                self.filter_panel.update_slider(event.pos)
                return True
        if event.type != pygame.KEYDOWN:
            return False

        if event.key == pygame.K_f and (pygame.key.get_mods() & pygame.KMOD_CTRL):
            self.state.search_active = not self.state.search_active
            return True

        if self.state.search_active and event.key not in (
            pygame.K_ESCAPE,
            pygame.K_RETURN,
            pygame.K_UP,
            pygame.K_DOWN,
        ):
            if event.key == pygame.K_BACKSPACE:
                self.state.search_query = self.state.search_query[:-1]
            elif event.unicode.isprintable():
                self.state.search_query += event.unicode
            self.apply_filters()
            return True

        original_idx = self.state.selected_idx
        if event.key == pygame.K_UP:
            self.state.selected_idx = max(0, self.state.selected_idx - 1)
        elif event.key == pygame.K_DOWN:
            self.state.selected_idx = min(len(self.filtered_list) - 1, self.state.selected_idx + 1)
        elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE) and not self.state.search_active:
            if self.state.current_view == "EPISODES":
                self.state.current_view = "RUNS"
                self.state.selected_run_path = None
                self.state.selected_run_name = None
                self.state.selected_idx = 0
                self.state.search_query = ""
                self.refresh_browser_list()
                return True
            else:
                self.controller.running = False
                return True
        elif event.key == pygame.K_RETURN and self.filtered_list:
            if self.state.search_active:
                self.state.search_active = False
                return True

            target_folder = self.filtered_list[self.state.selected_idx]
            if self.state.current_view == "RUNS":
                self.state.selected_run_path = target_folder
                self.state.selected_run_name = target_folder.name
                self.state.current_view = "EPISODES"
                self.state.selected_idx = 0
                self.state.search_query = ""
                self.refresh_browser_list()
            else:
                try:
                    session = load_from_storage(target_folder)
                    self.controller.switch_to_scene("PLAYBACK", session=session)
                except Exception as e:
                    self.controller.trigger_error(f"Reconstruction Halt Constraint: {e}")
            return True

        if self.state.selected_idx != original_idx:
            self.update_preview()
        return True

    def _handle_mouse_down(self, pos):
        ui = self.controller.ui

        if ui.x(40) <= pos[0] <= ui.x(200) and ui.y(70) <= pos[1] <= ui.y(105):
            self.state.show_filters = not self.state.show_filters
            return True

        if self.state.show_filters and self.state.current_view == "EPISODES":
            return self.filter_panel.handle_mouse_down(pos)
        return False

    def render(self, screen: pygame.Surface):
        screen.fill(BACKGROUND)
        self.controller.ui.update(screen)
        ui = self.controller.ui

        if not self.filtered_list and not self.runs_list and not self.episodes_list:
            title = self.controller.big_font.render("EMPTY REPOSITORY", True, ERROR_RED)
            msg = self.controller.font.render("No runs or episodes discovered.", True, TEXT_MUTED)
            screen.blit(
                title,
                title.get_rect(center=(ui.w(WINDOW_WIDTH) // 2, ui.h(WINDOW_HEIGHT) // 2 - ui.h(50))),
            )
            screen.blit(msg, msg.get_rect(center=(ui.w(WINDOW_WIDTH) // 2, ui.h(WINDOW_HEIGHT) // 2)))
            return

        title_str = "SYSTEM RUN BROWSER" if self.state.current_view == "RUNS" else f"RUN: {self.state.selected_run_name}"
        title = self.controller.big_font.render(title_str, True, ACCENT_CYAN)
        screen.blit(title, (ui.x(40), ui.y(25)))

        toggle_rect = pygame.Rect(ui.x(40), ui.y(70), ui.w(135), ui.h(32))
        pygame.draw.rect(screen, PANEL_BG, toggle_rect, border_radius=ui.r(6))
        pygame.draw.rect(screen, PANEL_BORDER, toggle_rect, width=max(1, ui.r(1)), border_radius=ui.r(6))
        toggle_text = self.controller.small_font.render(
            f"SIDE PANEL {'v' if self.state.show_filters else '>'}", True, ACCENT_CYAN
        )
        screen.blit(toggle_text, toggle_text.get_rect(center=toggle_rect.center))

        shortcuts = [
            ("↑↓", "Navigate"),
            ("ENTER", "Select Run" if self.state.current_view == "RUNS" else "Load Episode"),
            ("BACKSPACE", "Back to Runs" if self.state.current_view == "EPISODES" else "Exit"),
            ("Ctrl+F", "Filter"),
            ("ESC", "Back/Exit"),
        ]
        current_x = toggle_rect.right + ui.w(20)
        text_y_center = toggle_rect.y + toggle_rect.height // 2
        for key, action in shortcuts:
            key_render = self.controller.small_font.render(f"[{key}]", True, ACCENT_BLUE)
            screen.blit(key_render, (current_x, text_y_center - key_render.get_height() // 2))
            current_x += key_render.get_width() + ui.w(4)

            action_render = self.controller.small_font.render(action, True, TEXT_MUTED)
            screen.blit(action_render, (current_x, text_y_center - action_render.get_height() // 2))
            current_x += action_render.get_width() + ui.w(16)

        pygame.draw.line(
            screen,
            ACCENT_CYAN_DIM,
            (ui.x(40), ui.y(64)),
            (ui.w(WINDOW_WIDTH) - ui.x(40), ui.y(64)),
            max(1, ui.r(1)),
        )

        panel_x = ui.x(320) if self.state.show_filters else ui.x(35)
        panel_y = ui.y(110)
        panel_w = ui.w(WINDOW_WIDTH) - panel_x - ui.x(35)
        panel_h = ui.h(WINDOW_HEIGHT) - ui.y(165)
        left_pane_w = int(panel_w * 0.60)
        right_pane_x = panel_x + left_pane_w + ui.w(15)
        right_pane_w = panel_w - left_pane_w - ui.w(15)

        if self.state.show_filters and self.state.current_view == "EPISODES":
            self.filter_panel.render(screen)

        pygame.draw.rect(screen, PANEL_BG, (panel_x, panel_y, left_pane_w, panel_h), border_radius=ui.r(8))
        pygame.draw.rect(
            screen, PANEL_BORDER, (panel_x, panel_y, left_pane_w, panel_h), width=max(1, ui.r(1)), border_radius=ui.r(8)
        )

        self.episode_list_panel.render(screen, panel_x, panel_y, left_pane_w, panel_h)
        self.metadata_panel.render(screen, right_pane_x, panel_y, right_pane_w, panel_h)

        footer_y = ui.h(WINDOW_HEIGHT) - ui.y(42)
        pygame.draw.line(
            screen,
            DIVIDER_DARK,
            (ui.x(35), footer_y),
            (ui.w(WINDOW_WIDTH) - ui.x(35), footer_y),
            max(1, ui.r(1)),
        )

        label = "RUNS" if self.state.current_view == "RUNS" else "EPISODES"
        repo_count = f"{label} FOUND : {len(self.filtered_list)}"
        footer = self.controller.small_font.render(repo_count, True, TEXT_FOOTER)
        screen.blit(footer, (ui.x(40), footer_y + ui.y(10)))
# Update tools/episode_visualizer/controller.py to match this structure
import pygame
from tools.episode_visualizer.config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, BLACK, WHITE, GREEN, RED, GRAY
from tools.episode_visualizer.playback import Playback
from tools.episode_visualizer.renderer import Renderer
from tools.episode_visualizer.camera import Camera
from tools.episode_visualizer.overlays.hud import HUDOverlay
from tools.episode_visualizer.overlays.timeline import TimelineOverlay
from tools.episode_visualizer.overlays.graphs import GraphsOverlay
from tools.episode_visualizer.overlays.heading import HeadingOverlay
from tools.episode_visualizer.overlays.confidence import ConfidenceOverlay
from tools.episode_visualizer.input import handle_input
from core.memory.storage.browser import EpisodeBrowser
from tools.episode_visualizer.replay_loader import load_from_storage

class VisualizerController:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Subsystem Replay Visualizer Engine")
        self.clock = pygame.time.Clock()
        
        self.app_state = "BROWSER"
        self.error_message = ""
        self.show_guide = False
        
        self.browser_util = EpisodeBrowser()
        self.episodes_list = []
        self.selected_idx = 0
        self.font = pygame.font.SysFont(None, 24)
        
        self.session = None
        self.playback = None
        self.camera = Camera()
        self.renderer = Renderer(self.screen)
        
        # Instantiate overlays to modify visibilities using input hotkeys
        self.timeline_overlay = TimelineOverlay()
        self.graphs_overlay = GraphsOverlay()
        self.heading_overlay = HeadingOverlay()
        self.confidence_overlay = ConfidenceOverlay()
        
        self.overlays = [HUDOverlay(), self.timeline_overlay, self.graphs_overlay, self.heading_overlay, self.confidence_overlay]
        self.running = True
        self.refresh_browser_list()

    def refresh_browser_list(self):
        try:
            self.episodes_list = self.browser_util.list()
            self.selected_idx = 0
        except Exception as e:
            self.trigger_error(f"Failed listing target paths: {str(e)}")

    def trigger_error(self, message: str):
        self.error_message = message
        self.app_state = "ERROR"

    def load_session(self, session_obj):
        if session_obj and session_obj.validate():
            self.session = session_obj
            self.playback = Playback(session_obj)
            start_tick = session_obj.get_tick(0)
            if start_tick:
                self.camera.update(
                    target_pos=(start_tick.pos_x, start_tick.pos_y),
                    bounds=self.session.camera_bounds
                )
            self.app_state = "PLAYBACK"
        else:
            self.trigger_error("Loaded Session structural validation check failed.")

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            events = pygame.event.get()
            
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    continue
                
                if self.app_state == "BROWSER":
                    self.handle_browser_events(event)
                elif self.app_state == "ERROR":
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.app_state = "BROWSER"
                        self.refresh_browser_list()
                elif self.app_state == "PLAYBACK":
                    consumed = self.timeline_overlay.handle_event(event, self.playback)
                    if not consumed:
                        handle_input(event, self)

            if self.app_state == "PLAYBACK" and self.playback and not self.show_guide:
                self.playback.update(dt)
                current_tick = self.playback.get_current_tick()
                if current_tick and self.session:
                    self.camera.update(
                        target_pos=(current_tick.pos_x, current_tick.pos_y),
                        bounds=self.session.camera_bounds
                    )

            if self.app_state == "BROWSER":
                self.render_browser()
            elif self.app_state == "ERROR":
                self.render_error_screen()
            elif self.app_state == "PLAYBACK":
                self.renderer.render(self.session, self.playback, self.camera, self.overlays)
                if self.show_guide:
                    self.render_guide_screen()
                
            pygame.display.flip()
        pygame.quit()

    def handle_browser_events(self, event):
        if event.type != pygame.KEYDOWN:
            return
            
        if event.key == pygame.K_F1:
            self.show_guide = not self.show_guide
            return

        if self.show_guide:
            return

        if event.key == pygame.K_UP:
            self.selected_idx = max(0, self.selected_idx - 1)
        elif event.key == pygame.K_DOWN:
            self.selected_idx = min(len(self.episodes_list) - 1, self.selected_idx + 1)
        elif event.key == pygame.K_RETURN and self.episodes_list:
            try:
                target_folder = self.episodes_list[self.selected_idx]
                session = load_from_storage(target_folder)
                self.load_session(session)
            except Exception as e:
                self.trigger_error(f"Reconstruction Halt Constraint: {str(e)}")

    def render_browser(self):
        self.screen.fill(BLACK)
        if not self.episodes_list:
            lbl = self.font.render("EMPTY REPOSITORY ENCOUNTERED: No playable episodes discovered.", True, RED)
            esc = self.font.render("Press F1 to check context rules.", True, WHITE)
            self.screen.blit(lbl, (50, WINDOW_HEIGHT // 2))
            self.screen.blit(esc, (50, (WINDOW_HEIGHT // 2) + 40))
            if self.show_guide: self.render_guide_screen()
            return

        title = self.font.render("SYSTEM EPISODE BROWSER (UP/DOWN to navigate, ENTER to select, F1 for Help Guide)", True, WHITE)
        self.screen.blit(title, (30, 30))
        
        y_pos = 80
        for idx, path in enumerate(self.episodes_list):
            color = GREEN if idx == self.selected_idx else WHITE
            prefix = "> " if idx == self.selected_idx else "  "
            item_surf = self.font.render(f"{prefix}[{idx}] {path.name}", True, color)
            self.screen.blit(item_surf, (50, y_pos))
            y_pos += 30
            
        if self.show_guide:
            self.render_guide_screen()

    def render_error_screen(self):
        self.screen.fill(BLACK)
        err_title = self.font.render("CRITICAL VERIFICATION HALT ERROR", True, RED)
        err_msg = self.font.render(self.error_message, True, WHITE)
        esc_msg = self.font.render("Press ESC to drop session and return to Browser", True, WHITE)
        
        self.screen.blit(err_title, (30, 50))
        self.screen.blit(err_msg, (30, 100))
        self.screen.blit(esc_msg, (30, 150))

    def render_guide_screen(self):
        guide_surface = pygame.Surface((600, 450))
        guide_surface.fill((20, 20, 20))
        pygame.draw.rect(guide_surface, GRAY, guide_surface.get_rect(), 2)
        
        commands = [
            "SYSTEM DIAGNOSTIC KEYBIND GUIDE (Press F1 to exit)",
            "==================================================",
            "SPACE       - Toggle Play/Pause",
            "R           - Restart Episode",
            "L           - Toggle Loop playback",
            "LEFT/RIGHT  - Step Step frames back/forward",
            "UP/DOWN     - Adjust Playback Speed acceleration",
            "1, 2, 3     - Camera Tracking Mode (Follow, Static, Fit)",
            "H           - Toggle Heading Indicator line",
            "T           - Toggle Location Tracking Trail path",
            "G           - Toggle Emotion Metrics Canvas Grid",
            "C           - Toggle Anchor Point Confidence View",
            "ESC         - Return to Main Selection Browser view"
        ]
        
        for idx, line in enumerate(commands):
            color = GREEN if idx == 0 else WHITE
            txt = self.font.render(line, True, color)
            guide_surface.blit(txt, (20, 20 + idx * 30))
            
        self.screen.blit(guide_surface, (WINDOW_WIDTH // 2 - 300, WINDOW_HEIGHT // 2 - 225))
import pygame
import traceback
from tools.episode_visualizer.config import (WINDOW_WIDTH, WINDOW_HEIGHT, FPS, BACKGROUND)

from tools.episode_visualizer.scenes.browser import BrowserScene
from tools.episode_visualizer.scenes.playback import PlaybackScene
from tools.episode_visualizer.scenes.error import ErrorScene
from tools.episode_visualizer.overlays.guide import GuideOverlay


class UIScaler:
    def __init__(self):
        self.sx = 1.0
        self.sy = 1.0

    def update(self, screen):
        self.sx = screen.get_width() / WINDOW_WIDTH
        self.sy = screen.get_height() / WINDOW_HEIGHT

    def x(self, value):
        return int(round(value * self.sx))

    def y(self, value):
        return int(round(value * self.sy))

    def w(self, value):
        return max(1, int(round(value * self.sx)))

    def h(self, value):
        return max(1, int(round(value * self.sy)))

    def r(self, value):
        return max(1, int(round(min(self.sx, self.sy) * value)))
class VisualizerController:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
    (WINDOW_WIDTH, WINDOW_HEIGHT), 
    pygame.RESIZABLE
)
        pygame.display.set_caption("Subsystem Replay Visualizer Engine")
        self.clock = pygame.time.Clock()
        self.ui = UIScaler()
        
        self.font = pygame.font.SysFont("Consolas", 22)
        self.big_font = pygame.font.SysFont("Consolas", 34, bold=True)
        self.small_font = pygame.font.SysFont("Consolas", 18)

        self.guide_overlay = GuideOverlay(self)
        self.show_guide = False

        # Alias properties providing cross-compatibility with legacy/external input code definitions
        self.playback = None 

        self.scenes = {
            "BROWSER": BrowserScene(self),
            "PLAYBACK": PlaybackScene(self),
            "ERROR": ErrorScene(self)
        }
        self.active_scene = self.scenes["BROWSER"]
        self.running = True

    def switch_to_scene(self, scene_key: str, **kwargs):
        self.active_scene = self.scenes[scene_key]
        
        # Dynamic proxy reference sync tracking
        if scene_key == "PLAYBACK" and hasattr(self.active_scene, "playback"):
            self.playback = self.active_scene.playback
        else:
            self.playback = None

        if hasattr(self.active_scene, "on_enter"):
            self.active_scene.on_enter(**kwargs)

    def trigger_error(self, message: str):
        self.switch_to_scene("ERROR", error_message=message)

    def run(self):
        while self.running:
            try:
                dt = self.clock.tick(FPS) / 1000.0
                events = pygame.event.get()
                
                for event in events:
                    if event.type == pygame.QUIT:
                        self.running = False
                        continue
                    
                    # Intercept window scaling adjustments
                    if event.type == pygame.VIDEORESIZE:
                        # Re-initialize the video mode with the new dynamic constraints
                        self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                        
                        # Forward sizing changes down to the active scene if it needs an update
                        if hasattr(self.active_scene, "on_resize"):
                            self.active_scene.on_resize(event.w, event.h)
                        continue
                    
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                        self.show_guide = not self.show_guide
                        continue

                    if self.show_guide:
                        continue

                    self.active_scene.handle_event(event)

                if not self.show_guide:
                    # Sync proxy backward compatibility map right before running external update cycles
                    if self.active_scene == self.scenes["PLAYBACK"]:
                        self.playback = self.scenes["PLAYBACK"].playback
                    self.active_scene.update(dt)

                self.screen.fill(BACKGROUND)
                self.active_scene.render(self.screen)
                
                if self.show_guide:
                    self.guide_overlay.render(self.screen)
                    
                pygame.display.flip()
                
            except Exception as e:
                # Intercept every crash vector across frame processing execution hooks
                error_trace = traceback.format_exc()
                print(f"[ENGINE EXCEPTION ENCOUNTERED]\n{error_trace}") # Log output console details
                self.trigger_error(f"Runtime Crash Intercepted:\n{str(e)}")

        pygame.quit()
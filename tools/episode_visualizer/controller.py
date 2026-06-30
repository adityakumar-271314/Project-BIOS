import pygame
from tools.episode_visualizer.config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS
from tools.episode_visualizer.replay_session import ReplaySession
from tools.episode_visualizer.playback import Playback
from tools.episode_visualizer.renderer import Renderer
from tools.episode_visualizer.overlays import HUDOverlay, TimelineOverlay, GraphsOverlay
from tools.episode_visualizer.input import handle_input

class VisualizerController:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Subsystem Replay Visualizer Engine")
        self.clock = pygame.time.Clock()
        
        self.session = None
        self.playback = None
        self.renderer = Renderer(self.screen)
        
        self.timeline_overlay = TimelineOverlay()
        self.overlays = [
            HUDOverlay(),
            self.timeline_overlay,
            GraphsOverlay()
        ]
        self.running = True

    def load_session(self, session: ReplaySession):
        """Loads a valid architectural immutable ReplaySession boundary object."""
        if session and session.validate():
            self.session = session
            self.playback = Playback(session)
        else:
            print("[Visualizer Error] Provided session frame records validation failed.")

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    
                # 1. First feed mouse actions down directly into timeline layout handler
                consumed = self.timeline_overlay.handle_event(event, self.playback)
                
                # 2. If timeline didn't process it, let system general key input catch it
                if not consumed:
                    handle_input(event, self)

            # Continuous clock step logic tick tracking updates
            if self.playback:
                self.playback.update(dt)
                
            # Perform screen clears and pipeline draw calls
            self.renderer.render(self.session, self.playback, self.overlays)
            pygame.display.flip()
            
        pygame.quit()
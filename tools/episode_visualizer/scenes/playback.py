import pygame
from tools.episode_visualizer.scenes.base import Scene
from tools.episode_visualizer.playback import Playback
from tools.episode_visualizer.camera import Camera
from tools.episode_visualizer.renderer import Renderer
from tools.episode_visualizer.input import (
    handle_playback_input,
)  # Import renamed function

# Import specific dashboard telemetry modules
from tools.episode_visualizer.overlays.hud import HUDOverlay
from tools.episode_visualizer.overlays.timeline import TimelineOverlay
from tools.episode_visualizer.overlays.graphs import GraphsOverlay
from tools.episode_visualizer.overlays.heading import HeadingOverlay
from tools.episode_visualizer.overlays.confidence import ConfidenceOverlay


class PlaybackScene(Scene):
    def __init__(self, controller):
        super().__init__(controller)
        self.session = None
        self.playback = None
        self.camera = Camera()
        self.renderer = Renderer(self.controller.screen)

        self.hud_overlay = HUDOverlay()
        self.timeline_overlay = TimelineOverlay()
        self.graphs_overlay = GraphsOverlay()
        self.heading_overlay = HeadingOverlay()
        self.confidence_overlay = ConfidenceOverlay()

        self.overlays = [
            self.hud_overlay,
            self.timeline_overlay,
            self.graphs_overlay,
            self.heading_overlay,
            self.confidence_overlay,
        ]

    def on_enter(self, **kwargs):
        session_obj = kwargs.get("session")
        if session_obj and session_obj.validate():
            self.session = session_obj
            self.playback = Playback(session_obj)
            start_tick = session_obj.get_tick(0)
            if start_tick:
                self.camera.update(
                    target_pos=(start_tick.pos_x, start_tick.pos_y),
                    bounds=self.session.camera_bounds,
                )
        else:
            self.controller.trigger_error(
                "Loaded Session structural validation check failed."
            )

    def handle_event(self, event: pygame.event.Event):

        consumed = self.timeline_overlay.handle_event(event, self.playback)
        if not consumed:
            consumed = handle_playback_input(event, self)
        return consumed

    def update(self, dt: float):
        if self.playback:
            self.playback.update(dt)
            current_tick = self.playback.get_current_tick()
            if current_tick and self.session:
                self.camera.update(
                    target_pos=(current_tick.pos_x, current_tick.pos_y),
                    bounds=self.session.camera_bounds,
                )

    def render(self, screen: pygame.Surface):
        if self.session and self.playback:
            # Sync controller scaler matrix with current display layout boundaries
            self.controller.ui.update(screen)
            self.renderer.render(
                self.session,
                self.playback,
                self.camera,
                self.overlays,
                ui=self.controller.ui,
            )

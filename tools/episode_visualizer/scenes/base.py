import pygame


class Scene:
    def __init__(self, controller):
        self.controller = controller

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Process incoming Pygame events. Return True if event was consumed."""
        return False

    def update(self, dt: float):
        """Update scene physics, timers, tracking indicators, or state."""
        pass

    def render(self, screen: pygame.Surface):
        """Draw scene elements directly to the active screen buffer."""
        pass

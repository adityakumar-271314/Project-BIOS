import math

import pygame
from requests import session
from tools.episode_visualizer.config import BLACK, RED, YELLOW, GRAY, BLUE, AGENT_COLOR, AGENT_SIZE, HUD_FONT_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT
from tools.episode_visualizer.camera import Camera

class Renderer:
    """Strictly read-only rendering pipeline"""
    def __init__(self, screen):
        self.screen = screen
        self.camera = Camera()
        self.font = pygame.font.SysFont(None, HUD_FONT_SIZE)
        
        try:
            self.agent_sprite = pygame.Surface((AGENT_SIZE, AGENT_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(self.agent_sprite, AGENT_COLOR, (AGENT_SIZE // 2, AGENT_SIZE // 2), AGENT_SIZE // 2)
        except:
            self.agent_sprite = None

    def render(self, session, playback, overlays=None):
        self.screen.fill(BLACK)
        
        if not session or not playback:
            self.render_error("No replay session loaded")
            return
            
        current_tick = playback.get_current_tick()
        if not current_tick:
            return

        # Update camera focus to follow agent position
        pos_x = current_tick.get('pos_x', 0.0)
        pos_y = current_tick.get('pos_y', 0.0)
        self.camera.update(target_pos=(pos_x, pos_y))

        # Render World Grid Layout
        self.render_grid()
        


        if playback.current_frame > 0:
            trail_points = []
            # Collect all screen coordinates from frame 0 up to the current frame
            for f_idx in range(playback.current_frame + 1):
                t_data = session.get_tick(f_idx)
                if t_data:
                    tx = t_data.get('pos_x', 0.0)
                    ty = t_data.get('pos_y', 0.0)
                    trail_points.append(self.camera.world_to_screen(tx, ty))
            
            # Draw the historical line path if we have at least 2 points
            if len(trail_points) > 1:
                pygame.draw.lines(self.screen, GRAY, False, trail_points, 2)

        # --- Draw Start Point Indicator ---
        start_tick = session.get_tick(0)
        if start_tick:
            start_pos = self.camera.world_to_screen(start_tick.get('pos_x', 0.0), start_tick.get('pos_y', 0.0))
            pygame.draw.circle(self.screen, BLUE, start_pos, 6)  # Blue dot for start



        # Render Agent
        screen_pos = self.camera.world_to_screen(pos_x, pos_y)
        if self.agent_sprite:
            rect = self.agent_sprite.get_rect(center=screen_pos)
            self.screen.blit(self.agent_sprite, rect)
        else:
            pygame.draw.circle(self.screen, AGENT_COLOR, screen_pos, 20)
        heading_rad = current_tick.get('heading', 0.0)
        heading_deg = math.degrees(heading_rad)

        # Render Heading Vector Direction
        vector = pygame.math.Vector2(30, 0).rotate(heading_deg)
        end_pos = (screen_pos[0] + vector.x, screen_pos[1] + vector.y)
        pygame.draw.line(self.screen, YELLOW, screen_pos, end_pos, 3)
        # Dispatch registered overlays
        if overlays:
            for overlay in overlays:
                overlay.render(self.screen, session, playback, self.camera)

    # Inside tools/visualizer/renderer.py
    def render_grid(self):
        """Renders a grid overlay based on the current camera view."""
        
        # Get current top-left and bottom-right bounds of the screen in world coordinates
        top_left_world = self.camera.screen_to_world(0, 0)
        bottom_right_world = self.camera.screen_to_world(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        grid_size = 10  # Draw a grid line every 10 world units
        
        start_x = int(top_left_world[0] // grid_size) * grid_size
        end_x = int(bottom_right_world[0] // grid_size) * grid_size
        start_y = int(top_left_world[1] // grid_size) * grid_size
        end_y = int(bottom_right_world[1] // grid_size) * grid_size
        
        # Draw vertical grid lines
        for x in range(int(start_x), int(end_x) + grid_size, grid_size):
            p1 = self.camera.world_to_screen(x, top_left_world[1])
            p2 = self.camera.world_to_screen(x, bottom_right_world[1])
            pygame.draw.line(self.screen, (30, 30, 30), p1, p2, 1)
            
        # Draw horizontal grid lines
        for y in range(int(start_y), int(end_y) + grid_size, grid_size):
            p1 = self.camera.world_to_screen(top_left_world[0], y)
            p2 = self.camera.world_to_screen(bottom_right_world[0], y)
            pygame.draw.line(self.screen, (30, 30, 30), p1, p2, 1)

    def render_error(self, msg: str):
        text = self.font.render(msg, True, RED)
        self.screen.blit(text, (WINDOW_WIDTH // 2 - text.get_width() // 2, WINDOW_HEIGHT // 2))
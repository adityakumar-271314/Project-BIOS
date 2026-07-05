import math
import pygame
from tools.episode_visualizer.assets import AssetManager
from tools.episode_visualizer.config import RED, WHITE, GRAY, BLUE, AGENT_COLOR, WINDOW_WIDTH, WINDOW_HEIGHT

class Renderer:
    """Strictly read-only rendering pipeline divided into isolated drawing passes."""
    def __init__(self, screen):
        self.screen = screen
        self.assets = AssetManager()

    def render(self, session, playback, camera, overlays=None):
        self.screen.fill(WHITE)
        
        if not session or not playback:
            return
            
        current_tick = playback.get_current_tick()
        if not current_tick:
            return

        # Explicit rendering steps execution flow
        self.render_grid(camera)
        self.render_path(session, playback.current_frame, camera)
        self.render_markers(session, camera)
        self.render_agent(current_tick, camera)

        # Dispatch registered diagnostic presentation overlays
        if overlays:
            for overlay in overlays:
                overlay.render(self.screen, session, playback, camera)

    def render_grid(self, camera):
        top_left_world = camera.screen_to_world(0, 0)
        bottom_right_world = camera.screen_to_world(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        grid_size = 10
        start_x = int(top_left_world[0] // grid_size) * grid_size
        end_x = int(bottom_right_world[0] // grid_size) * grid_size
        start_y = int(top_left_world[1] // grid_size) * grid_size
        end_y = int(bottom_right_world[1] // grid_size) * grid_size
        
        for x in range(start_x, end_x + grid_size, grid_size):
            p1 = camera.world_to_screen(x, top_left_world[1])
            p2 = camera.world_to_screen(x, bottom_right_world[1])
            pygame.draw.line(self.screen, (230, 230, 230), p1, p2, 1)
            
        for y in range(start_y, end_y + grid_size, grid_size):
            p1 = camera.world_to_screen(top_left_world[0], y)
            p2 = camera.world_to_screen(bottom_right_world[0], y)
            pygame.draw.line(self.screen, (230, 230, 230), p1, p2, 1)

    def render_path(self, session, current_frame: int, camera):
        if current_frame <= 0:
            return
            
        trail_points = []
        for f_idx in range(current_frame + 1):
            t_data = session.get_tick(f_idx)
            if t_data:
                trail_points.append(camera.world_to_screen(t_data.pos_x, t_data.pos_y))
        
        if len(trail_points) > 1:
            pygame.draw.lines(self.screen, GRAY, False, trail_points, 2)

    def render_markers(self, session, camera):
        start_tick = session.get_tick(0)
        if start_tick:
            start_pos = camera.world_to_screen(start_tick.pos_x, start_tick.pos_y)
            pygame.draw.circle(self.screen, BLUE, start_pos, 6)

    def render_agent(self, tick, camera):
        screen_pos = camera.world_to_screen(tick.pos_x, tick.pos_y)
        agent_surf = self.assets.get_agent_sprite()

        if agent_surf:
            heading_deg = math.degrees(tick.heading)
            # Match standard asset rotation tracking schemas (counter-clockwise correction)
            rotated_agent = pygame.transform.rotate(agent_surf, -heading_deg)
            rect = rotated_agent.get_rect(center=screen_pos)
            self.screen.blit(rotated_agent, rect)
        else:
            pygame.draw.circle(self.screen, AGENT_COLOR, screen_pos, 20)
import pygame
from tools.episode_visualizer.assets import AssetManager
from tools.episode_visualizer.config import RED, WHITE, GRAY, BLUE, GREEN, AGENT_COLOR, WINDOW_WIDTH, WINDOW_HEIGHT

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.assets = AssetManager()
        self.trail_visible = True

    def render(self, session, playback, camera, overlays=None):
        self.screen.fill(WHITE)
        if not session or not playback:
            return
            
        current_tick = playback.get_current_tick()
        if not current_tick:
            return

        self.render_grid(camera)
        
        if self.trail_visible:
            self.render_path(session, playback.current_frame, camera)
            
        self.render_markers(session, camera)
        self.render_agent(current_tick, camera)

        if overlays:
            for overlay in overlays:
                overlay.render(self.screen, session, playback, camera)

    def render_grid(self, camera):
        top_left = camera.screen_to_world(0, 0)
        bottom_right = camera.screen_to_world(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        grid_size = 10
        start_x = int(top_left[0] // grid_size) * grid_size
        end_x = int(bottom_right[0] // grid_size) * grid_size
        start_y = int(top_left[1] // grid_size) * grid_size
        end_y = int(bottom_right[1] // grid_size) * grid_size
        
        for x in range(start_x, end_x + grid_size, grid_size):
            p1 = camera.world_to_screen(x, top_left[1])
            p2 = camera.world_to_screen(x, bottom_right[1])
            pygame.draw.line(self.screen, (240, 240, 240), p1, p2, 1)
            
        for y in range(start_y, end_y + grid_size, grid_size):
            p1 = camera.world_to_screen(top_left[0], y)
            p2 = camera.world_to_screen(bottom_right[0], y)
            pygame.draw.line(self.screen, (240, 240, 240), p1, p2, 1)

    def render_path(self, session, current_frame: int, camera):
        if current_frame <= 0:
            return
        trail_points = [camera.world_to_screen(t.pos_x, t.pos_y) for f_idx in range(current_frame + 1) if (t := session.get_tick(f_idx))]
        if len(trail_points) > 1:
            pygame.draw.lines(self.screen, GRAY, False, trail_points, 2)

    def render_markers(self, session, camera):
        # Start point (Blue)
        if start_tick := session.get_tick(0):
            p_start = camera.world_to_screen(start_tick.pos_x, start_tick.pos_y)
            pygame.draw.circle(self.screen, BLUE, p_start, 8)
            pygame.draw.circle(self.screen, WHITE, p_start, 4)

        # Finish point (Green Indicator Outline)
        if finish_tick := session.get_tick(len(session.ticks) - 1):
            p_end = camera.world_to_screen(finish_tick.pos_x, finish_tick.pos_y)
            pygame.draw.circle(self.screen, GREEN, p_end, 8)
            pygame.draw.circle(self.screen, WHITE, p_end, 4)

    def render_agent(self, tick, camera):
        screen_pos = camera.world_to_screen(tick.pos_x, tick.pos_y)
        agent_surf = self.assets.get_agent_sprite()
        if agent_surf:
            import math
            heading_deg = math.degrees(tick.heading)
            rotated_agent = pygame.transform.rotate(agent_surf, -heading_deg)
            rect = rotated_agent.get_rect(center=screen_pos)
            self.screen.blit(rotated_agent, rect)
        else:
            pygame.draw.circle(self.screen, AGENT_COLOR, screen_pos, 20)
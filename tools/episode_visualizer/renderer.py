import pygame
from tools.episode_visualizer.assets import AssetManager
from tools.episode_visualizer.config import RED, VERY_LIGHT_GRAY, WHITE, GRAY, BLUE, GREEN, AGENT_COLOR, ORANGE

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.assets = AssetManager()
        self.trail_visible = True
        self.raw_visible = True

    def render(self, session, playback, camera, overlays=None, ui=None):
        # Dynamically sample container bounds to support real-time resizing
        screen_w, screen_h = self.screen.get_size()
        self.screen.fill(WHITE)
        
        if not session or not playback:
            return
            
        current_tick = playback.get_current_tick()
        if not current_tick:
            return

        # Inject runtime spatial constants into camera state calculation
        camera.update_dimensions(screen_w, screen_h)

        self.render_grid(camera, screen_w, screen_h, ui)
        
        if self.raw_visible and session.raw_path:
            self.render_raw_telemetry_path(session, camera, ui)
            self.render_drift_vector(session, playback.current_frame, camera, ui)

        if self.trail_visible:
            self.render_path(session, playback.current_frame, camera, ui)
            
        self.render_markers(session, camera, ui)
        self.render_agent(current_tick, camera, ui)

        if overlays:
            for overlay in overlays:
                overlay.render(self.screen, session, playback, camera, ui)

    def render_grid(self, camera, screen_w, screen_h, ui):
        top_left = camera.screen_to_world(0, 0)
        bottom_right = camera.screen_to_world(screen_w, screen_h)
        
        grid_size = 10
        start_x = int(top_left[0] // grid_size) * grid_size
        end_x = int(bottom_right[0] // grid_size) * grid_size
        start_y = int(top_left[1] // grid_size) * grid_size
        end_y = int(bottom_right[1] // grid_size) * grid_size
        
        line_thickness = ui.w(1) if ui else 1
        
        for x in range(start_x, end_x + grid_size, grid_size):
            p1 = camera.world_to_screen(x, top_left[1])
            p2 = camera.world_to_screen(x, bottom_right[1])
            pygame.draw.line(self.screen, VERY_LIGHT_GRAY, p1, p2, line_thickness)
            
        for y in range(start_y, end_y + grid_size, grid_size):
            p1 = camera.world_to_screen(top_left[0], y)
            p2 = camera.world_to_screen(bottom_right[0], y)
            pygame.draw.line(self.screen, VERY_LIGHT_GRAY, p1, p2, line_thickness)

    def render_path(self, session, current_frame: int, camera, ui):
        if current_frame <= 0:
            return
        trail_points = [camera.world_to_screen(t.pos_x, t.pos_y) for f_idx in range(current_frame + 1) if (t := session.get_tick(f_idx))]
        if len(trail_points) > 1:
            pygame.draw.lines(self.screen, GRAY, False, trail_points, ui.w(2) if ui else 2)

    def render_markers(self, session, camera, ui):
        outer_r = ui.r(8) if ui else 8
        inner_r = ui.r(4) if ui else 4

        if start_tick := session.get_tick(0):
            p_start = camera.world_to_screen(start_tick.pos_x, start_tick.pos_y)
            pygame.draw.circle(self.screen, BLUE, p_start, outer_r)
            pygame.draw.circle(self.screen, WHITE, p_start, inner_r)

        if finish_tick := session.get_tick(len(session.ticks) - 1):
            p_end = camera.world_to_screen(finish_tick.pos_x, finish_tick.pos_y)
            pygame.draw.circle(self.screen, GREEN, p_end, outer_r)
            pygame.draw.circle(self.screen, WHITE, p_end, inner_r)

    def render_agent(self, tick, camera, ui):
        screen_pos = camera.world_to_screen(tick.pos_x, tick.pos_y)
        agent_surf = self.assets.get_agent_sprite()
        if agent_surf:
            import math
            heading_deg = math.degrees(tick.heading)
            # Scaling sprite geometry dynamically using the radius scalar context
            if ui:
                target_size = ui.r(40)
                agent_surf = pygame.transform.scale(agent_surf, (target_size, target_size))
            rotated_agent = pygame.transform.rotate(agent_surf, -heading_deg)
            rect = rotated_agent.get_rect(center=screen_pos)
            self.screen.blit(rotated_agent, rect)
        else:
            pygame.draw.circle(self.screen, AGENT_COLOR, screen_pos, ui.r(20) if ui else 20)

    def render_raw_telemetry_path(self, session, camera, ui):
        raw_points = [camera.world_to_screen(pos[0], pos[1]) for pos in session.raw_path]
        if len(raw_points) > 1:
            pygame.draw.lines(self.screen, ORANGE, False, raw_points, ui.w(1) if ui else 1)

    def render_drift_vector(self, session, current_frame: int, camera, ui):
        if current_frame < len(session.raw_path):
            tick = session.get_tick(current_frame)
            raw_pos = session.raw_path[current_frame]
            
            p_est = camera.world_to_screen(tick.pos_x, tick.pos_y)
            p_raw = camera.world_to_screen(raw_pos[0], raw_pos[1])
            
            if tick.drift > 0.1:
                pygame.draw.line(self.screen, RED, p_est, p_raw, ui.w(1) if ui else 1)
                pygame.draw.circle(self.screen, RED, p_raw, ui.r(3) if ui else 3)
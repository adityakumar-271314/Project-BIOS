import pygame
from tools.episode_visualizer.config import GRAY, TIMELINE_HEIGHT, DARK_GRAY, WHITE, RED, GREEN, BLUE, YELLOW

class GraphsOverlay:
    def __init__(self):
        self.visible = True
        self.base_font_size = 14
        self.font = pygame.font.SysFont("Consolas", self.base_font_size)
        self.base_height = 190
        
        self.colors = {
            "fear": RED,
            "stress": (255, 128, 0),
            "drive": BLUE,
            "energy": GREEN,
            "integrity": YELLOW
        }

    def render(self, screen, session, playback, camera, ui=None):
        if not self.visible or not session or playback.total_frames == 0:
            return
            
        screen_w, screen_h = screen.get_size()
        timeline_h = ui.h(TIMELINE_HEIGHT) if ui else TIMELINE_HEIGHT
        graph_h = ui.h(self.base_height) if ui else self.base_height
        
        # --- NARROWED WINDOW EDGE GAPS ---
        pad_x = ui.x(6) if ui else 6  # Reduced gap to bring box closer to window edge
        pad_bottom = ui.h(6) if ui else 6
        box_w = screen_w - (pad_x * 2)
        box_h = graph_h
        
        y_top = screen_h - timeline_h - box_h - pad_bottom
        
        if ui:
            self.font = pygame.font.SysFont("Consolas", ui.r(self.base_font_size))

        # --- THICKENED OUTSIDE BORDERS ---
        radius = ui.r(10) if ui else 10
        border_thickness_1 = ui.w(3) if ui else 3
        border_thickness_2 = ui.w(2) if ui else 2
        
        # Layer 1: Strong outer shadow base
        pygame.draw.rect(screen, (8, 9, 12), (pad_x, y_top + 2, box_w, box_h), border_radius=radius)
        # Layer 2: Core graph canvas frame
        pygame.draw.rect(screen, (18, 19, 26), (pad_x, y_top, box_w, box_h), border_radius=radius)
        # Layer 3: Thickened structural border accent
        pygame.draw.rect(screen, (35, 38, 50), (pad_x, y_top, box_w, box_h), width=border_thickness_1, border_radius=radius)
        # Layer 4: Tight inner shadow ridge for precise physical depth
        pygame.draw.rect(screen, (55, 60, 78), (pad_x + 2, y_top + 2, box_w - 4, box_h - 4), width=border_thickness_2, border_radius=radius)

        # --- GRAPH LAYOUT BOUNDS ---
        axis_left_margin = ui.x(45) if ui else 45
        axis_right_margin = ui.x(45) if ui else 45
        axis_bottom_pad = ui.h(20) if ui else 20
        legend_deck_height = ui.h(38) if ui else 38
        
        graph_canvas_w = box_w - axis_left_margin - axis_right_margin
        graph_canvas_h = box_h - legend_deck_height - axis_bottom_pad
        
        graph_origin_y = y_top + legend_deck_height
        y_zero = graph_origin_y + graph_canvas_h

        # Sub-surface clipping environment
        graph_surface = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        
        # Clear isolated vertical axis baseline
        pygame.draw.line(graph_surface, (65, 70, 95), (axis_left_margin, legend_deck_height), (axis_left_margin, y_zero - y_top), ui.w(2) if ui else 2)

        # Internal gridlines construction
        for val in [0.0, 0.5, 1.0]:
            internal_y = int((y_zero - y_top) - (val * graph_canvas_h))
            pygame.draw.line(graph_surface, (28, 30, 42), (axis_left_margin, internal_y), (box_w - axis_right_margin, internal_y), ui.w(1) if ui else 1)
            
            lbl = self.font.render(f"{val:.1f}", True, (110, 120, 140))
            graph_surface.blit(lbl, (axis_left_margin - (ui.x(32) if ui else 32), internal_y - (ui.y(6) if ui else 6)))

        # --- METRICS COLLECTION AND SIMULATION ---
        curr_frame = playback.current_frame
        metrics = {k: [] for k in self.colors.keys()}
        peaks = {k: (-1, -1.0) for k in self.colors.keys()}

        for f_idx in range(curr_frame + 1):
            t = session.get_tick(f_idx)
            if t:
                for key in self.colors.keys():
                    val = getattr(t, key)
                    metrics[key].append(val)
                    if val > peaks[key][1]:
                        peaks[key] = (f_idx, val)

        x_step = graph_canvas_w / (playback.total_frames - 1) if playback.total_frames > 1 else 1

        for name, values in metrics.items():
            if len(values) <= 1:
                continue
            
            points = []
            for i, val in enumerate(values):
                x = int(axis_left_margin + (i * x_step))
                norm_val = max(0.0, min(float(val), 1.0))
                y = int((y_zero - y_top) - (norm_val * graph_canvas_h))
                points.append((x, y))
            
            color = self.colors[name]
            fill_color = (color[0], color[1], color[2], 18)
            poly_points = [(points[0][0], y_zero - y_top)] + points + [(points[-1][0], y_zero - y_top)]
            pygame.draw.polygon(graph_surface, fill_color, poly_points)

        # --- PASS 2: DRAW ALL SHARP FOREGROUND LINES & LEADING DOTS ON TOP ---
        for name, values in metrics.items():
            if not values:
                continue
                
            points = []
            for i, val in enumerate(values):
                x = int(axis_left_margin + (i * x_step))
                norm_val = max(0.0, min(float(val), 1.0))
                y = int((y_zero - y_top) - (norm_val * graph_canvas_h))
                points.append((x, y))
                
            color = self.colors[name]
            
            if len(points) == 1:
                pygame.draw.circle(graph_surface, color, points[0], ui.r(3) if ui else 3)
            elif len(points) > 1:
                # Draw the historical line track
                pygame.draw.lines(graph_surface, color, False, points, ui.w(2) if ui else 2)
                
                # Draw a leading edge indicator dot at the current frame (the last point)
                leading_point = points[-1]
                # Outer solid color dot
                pygame.draw.circle(graph_surface, color, leading_point, ui.r(4) if ui else 4)
                # Inner dark core to make it look sharp and modern against the background
                pygame.draw.circle(graph_surface, (18, 19, 26), leading_point, ui.r(1.5) if ui else 1.5)

        # Hollow Peak Identifiers
        for name, (peak_frame, peak_val) in peaks.items():
            if peak_frame != -1 and peak_val > 0.4:
                px = int(axis_left_margin + (peak_frame * x_step))
                py = int((y_zero - y_top) - (max(0.0, min(peak_val, 1.0)) * graph_canvas_h))
                
                # Ensure we don't try to draw outside current timeline runtime range
                if px <= int(axis_left_margin + (curr_frame * x_step)):
                    color = self.colors[name]
                    pygame.draw.circle(graph_surface, color, (px, py), ui.r(5) if ui else 5, ui.w(1) if ui else 1)
                    pygame.draw.circle(graph_surface, (18, 19, 26), (px, py), ui.r(2) if ui else 2)

        # Foreground playback scrubber hairline tracker
        head_x = int(axis_left_margin + (curr_frame * x_step))
        pygame.draw.line(graph_surface, (210, 225, 255), (head_x, legend_deck_height), (head_x, y_zero - y_top), ui.w(1) if ui else 1)

        # Blit nested surface back out to the master render pipeline viewport 
        screen.blit(graph_surface, (pad_x, y_top))

        # --- HIGHER-LIFTED TEXT LEGENDS ROW ---
        start_x = pad_x + axis_left_margin
        text_y = y_top + (ui.y(12) if ui else 12)
        step_x = ui.x(125) if ui else 125
        
        for idx, (name, color) in enumerate(self.colors.items()):
            curr_val = metrics[name][-1] if metrics[name] else 0.0
            x_pos = start_x + (idx * step_x)
            
            block_size = ui.r(6) if ui else 6
            block_y = text_y + (ui.y(4) if ui else 4)
            pygame.draw.rect(screen, color, (x_pos, block_y, block_size, block_size), border_radius=ui.r(1) if ui else 1)
            
            lbl = self.font.render(f" {name.lower()}: {curr_val:.2f}", True, (160, 175, 190))
            screen.blit(lbl, (x_pos + block_size, text_y))
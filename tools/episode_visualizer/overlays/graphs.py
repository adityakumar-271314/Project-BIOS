import pygame
from tools.episode_visualizer.config import WINDOW_WIDTH, WINDOW_HEIGHT, TIMELINE_HEIGHT, DARK_GRAY, WHITE, RED, GREEN, BLUE, YELLOW

class GraphsOverlay:
    def __init__(self):
        self.visible = True
        self.font = pygame.font.SysFont(None, 14)
        self.height = 120
        self.y_top = WINDOW_HEIGHT - TIMELINE_HEIGHT - self.height
        
        # Color mapping across core metric profiles
        self.colors = {
            "fear": RED,
            "stress": (255, 128, 0),  # Orange
            "drive": BLUE,
            "energy": GREEN,
            "integrity": YELLOW
        }

    def render(self, screen, session, playback, camera):
        if not self.visible or not session or playback.total_frames == 0:
            return
            
        # Draw background graph canvas panel bound box
        pygame.draw.rect(screen, DARK_GRAY, (0, self.y_top, WINDOW_WIDTH, self.height))
        pygame.draw.line(screen, WHITE, (0, self.y_top), (WINDOW_WIDTH, self.y_top), 1)
        
        curr_frame = playback.current_frame
        if curr_frame == 0:
            return

        # Extract architectural metrics series histories
        metrics = {k: [] for k in self.colors.keys()}
        for f_idx in range(curr_frame + 1):
            t = session.get_tick(f_idx)
            if t:
                metrics["fear"].append(t.fear)
                metrics["stress"].append(t.stress)
                metrics["drive"].append(t.drive)
                metrics["energy"].append(t.energy)
                metrics["integrity"].append(t.integrity)

        # Scale and render vector point lists
        x_step = WINDOW_WIDTH / (playback.total_frames - 1) if playback.total_frames > 1 else 1
        
        for name, values in metrics.items():
            if len(values) < 2:
                continue
                
            points = []
            for i, val in enumerate(values):
                x = int(i * x_step)
                # Norm metric value bounding (assumes structured normalized range 0.0 - 1.0)
                norm_val = max(0.0, min(float(val), 1.0))
                y = int(self.y_top + self.height - 15 - (norm_val * (self.height - 30)))
                points.append((x, y))
                
            if len(points) > 1:
                pygame.draw.lines(screen, self.colors[name], False, points, 2)

        # Draw a clear vertical playback head rule marker
        head_x = int(curr_frame * x_step)
        pygame.draw.line(screen, WHITE, (head_x, self.y_top), (head_x, self.y_top + self.height), 1)
        
        # Overlay standard descriptive legend labels
        spacing = 0
        for name, color in self.colors.items():
            lbl = self.font.render(name.upper(), True, color)
            screen.blit(lbl, (15 + spacing, self.y_top + 5))
            spacing += 80
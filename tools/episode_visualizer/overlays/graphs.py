import pygame
from tools.episode_visualizer.config import GRAY, WINDOW_WIDTH, WINDOW_HEIGHT, TIMELINE_HEIGHT, DARK_GRAY, WHITE, RED, GREEN, BLUE, YELLOW

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
        
        # Draw explicit baseline axes and normalized value markers
        for val in [0.0, 0.5, 1.0]:
            y_axis = int(self.y_top + self.height - 15 - (val * (self.height - 30)))
            pygame.draw.line(screen, (70, 70, 70), (0, y_axis), (WINDOW_WIDTH, y_axis), 1)
            lbl = self.font.render(f"{val:.1f}", True, GRAY)
            screen.blit(lbl, (WINDOW_WIDTH - 25, y_axis - 5))

        curr_frame = playback.current_frame
        metrics = {k: [] for k in self.colors.keys()}
        for f_idx in range(curr_frame + 1):
            t = session.get_tick(f_idx)
            if t:
                metrics["fear"].append(t.fear)
                metrics["stress"].append(t.stress)
                metrics["drive"].append(t.drive)
                metrics["energy"].append(t.energy)
                metrics["integrity"].append(t.integrity)

        x_step = WINDOW_WIDTH / (playback.total_frames - 1) if playback.total_frames > 1 else 1
        
        for name, values in metrics.items():
            if len(values) < 2:
                continue
            points = []
            for i, val in enumerate(values):
                x = int(i * x_step)
                norm_val = max(0.0, min(float(val), 1.0))
                y = int(self.y_top + self.height - 15 - (norm_val * (self.height - 30)))
                points.append((x, y))
            if len(points) > 1:
                pygame.draw.lines(screen, self.colors[name], False, points, 2)

        # Live playback head tracking line
        head_x = int(curr_frame * x_step)
        pygame.draw.line(screen, WHITE, (head_x, self.y_top), (head_x, self.y_top + self.height), 1)
        
        # Overlay standard descriptive legend labels
        spacing = 0
        for name, color in self.colors.items():
            lbl = self.font.render(name.upper(), True, color)
            screen.blit(lbl, (15 + spacing, self.y_top + 5))
            spacing += 80
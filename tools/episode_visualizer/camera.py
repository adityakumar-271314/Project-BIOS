from tools.episode_visualizer.config import PIXELS_PER_UNIT, WINDOW_WIDTH, WINDOW_HEIGHT

class Camera:
    def __init__(self):
        self.zoom = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.mode = "FOLLOW"  # Options: "FOLLOW", "STATIC", "FIT"

    def world_to_screen(self, world_x: float, world_y: float) -> tuple:
        screen_x = int((world_x - self.offset_x) * PIXELS_PER_UNIT * self.zoom + WINDOW_WIDTH / 2)
        screen_y = int((world_y - self.offset_y) * PIXELS_PER_UNIT * self.zoom + WINDOW_HEIGHT / 2)
        return (screen_x, screen_y)

    def screen_to_world(self, screen_x: int, screen_y: int) -> tuple:
        world_x = (screen_x - WINDOW_WIDTH / 2) / (PIXELS_PER_UNIT * self.zoom) + self.offset_x
        world_y = (screen_y - WINDOW_HEIGHT / 2) / (PIXELS_PER_UNIT * self.zoom) + self.offset_y
        return (world_x, world_y)

    def set_mode(self, mode: str):
        if mode in ["FOLLOW", "STATIC", "FIT"]:
            self.mode = mode

    def update(self, target_pos: tuple = None, bounds: tuple = None):
        """
        Calculates viewport positioning constraints strictly using incoming data frames.
        bounds format: (min_x, min_y, max_x, max_y)
        """
        if self.mode == "FOLLOW" and target_pos:
            self.offset_x = target_pos[0]
            self.offset_y = target_pos[1]
            
        elif self.mode == "FIT" and bounds:
            min_x, min_y, max_x, max_y = bounds
            self.offset_x = (min_x + max_x) / 2
            self.offset_y = (min_y + max_y) / 2
            
            world_w = max(1.0, max_x - min_x)
            world_h = max(1.0, max_y - min_y)
            
            zoom_x = (WINDOW_WIDTH * 0.85) / (world_w * PIXELS_PER_UNIT)
            zoom_y = (WINDOW_HEIGHT * 0.65) / (world_h * PIXELS_PER_UNIT)  # Extra vertical spacing for graph canvas
            
            self.zoom = max(0.2, min(zoom_x, zoom_y, 4.0))
            
        elif self.mode == "STATIC" and bounds and (self.offset_x == 0.0 and self.offset_y == 0.0):
            # Center map statically once on initialization boundaries
            min_x, min_y, max_x, max_y = bounds
            self.offset_x = (min_x + max_x) / 2
            self.offset_y = (min_y + max_y) / 2
            self.zoom = 1.0
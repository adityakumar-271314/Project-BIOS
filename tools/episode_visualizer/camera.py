from tools.episode_visualizer.config import PIXELS_PER_UNIT, WINDOW_WIDTH, WINDOW_HEIGHT


class Camera:
    def __init__(self):
        self.zoom = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.mode = "FOLLOW"
        self.reset_static = False
        # Manage viewport state internal definitions dynamically
        self.screen_w = WINDOW_WIDTH
        self.screen_h = WINDOW_HEIGHT

    def update_dimensions(self, width: int, height: int):
        self.screen_w = width
        self.screen_h = height

    def world_to_screen(self, world_x: float, world_y: float) -> tuple:
        screen_x = int(
            (world_x - self.offset_x) * PIXELS_PER_UNIT * self.zoom + self.screen_w / 2
        )
        screen_y = int(
            (world_y - self.offset_y) * PIXELS_PER_UNIT * self.zoom + self.screen_h / 2
        )
        return (screen_x, screen_y)

    def screen_to_world(self, screen_x: int, screen_y: int) -> tuple:
        world_x = (screen_x - self.screen_w / 2) / (
            PIXELS_PER_UNIT * self.zoom
        ) + self.offset_x
        world_y = (screen_y - self.screen_h / 2) / (
            PIXELS_PER_UNIT * self.zoom
        ) + self.offset_y
        return (world_x, world_y)

    def set_mode(self, mode: str):
        if mode in ["FOLLOW", "STATIC", "FIT"]:
            self.mode = mode

    def update(self, target_pos: tuple = None, bounds: tuple = None):
        if self.mode == "FOLLOW" and target_pos:
            self.offset_x = target_pos[0]
            self.offset_y = target_pos[1]

        elif self.mode == "FIT" and bounds:
            min_x, min_y, max_x, max_y = bounds
            self.offset_x = (min_x + max_x) / 2
            self.offset_y = (min_y + max_y) / 2

            world_w = max(1.0, max_x - min_x)
            world_h = max(1.0, max_y - min_y)

            zoom_x = (self.screen_w * 0.8) / (world_w * PIXELS_PER_UNIT)
            zoom_y = (self.screen_h * 0.5) / (world_h * PIXELS_PER_UNIT)

            self.zoom = max(0.1, min(zoom_x, zoom_y, 3.0))

        elif self.mode == "STATIC" and bounds:
            if self.reset_static or (self.offset_x == 0.0 and self.offset_y == 0.0):
                min_x, min_y, max_x, max_y = bounds
                self.offset_x = (min_x + max_x) / 2
                self.offset_y = (min_y + max_y) / 2
                self.zoom = 1.0
                self.reset_static = False

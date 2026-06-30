from tools.episode_visualizer.config import PIXELS_PER_UNIT, WINDOW_WIDTH, WINDOW_HEIGHT

class Camera:
    def __init__(self):
        self.zoom = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.follow_agent = True

    def world_to_screen(self, world_x: float, world_y: float) -> tuple:
        screen_x = int((world_x - self.offset_x) * PIXELS_PER_UNIT * self.zoom + WINDOW_WIDTH / 2)
        screen_y = int((world_y - self.offset_y) * PIXELS_PER_UNIT * self.zoom + WINDOW_HEIGHT / 2)
        return (screen_x, screen_y)

    def screen_to_world(self, screen_x: int, screen_y: int) -> tuple:
        world_x = (screen_x - WINDOW_WIDTH / 2) / (PIXELS_PER_UNIT * self.zoom) + self.offset_x
        world_y = (screen_y - WINDOW_HEIGHT / 2) / (PIXELS_PER_UNIT * self.zoom) + self.offset_y
        return (world_x, world_y)

    def update(self, target_pos=None, bounds=None):
        if self.follow_agent and target_pos:
            self.offset_x = target_pos[0]
            self.offset_y = target_pos[1]
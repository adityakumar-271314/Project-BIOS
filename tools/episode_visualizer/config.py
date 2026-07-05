import pygame

# Window and rendering constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FPS = 60

# Coordinate system (world units)
WORLD_ORIGIN = (0, 0)
PIXELS_PER_UNIT = 8  # Scale factor

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (220, 220, 220)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
DARK_GRAY = (40, 40, 40)

# Agent
AGENT_SIZE = 40
AGENT_COLOR = GREEN

# Overlays
HUD_FONT_SIZE = 18
TIMELINE_HEIGHT = 40
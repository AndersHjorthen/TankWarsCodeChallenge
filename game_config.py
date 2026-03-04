"""Centralized game configuration for TankWars.

All magic numbers and hardcoded values are collected here so that
game-wide tuning can be done from a single location.
"""
import math

# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------
DISPLAY_WIDTH = 1200
DISPLAY_HEIGHT = 800
GAME_FPS = 30
CLIENT_FPS = 60
INTRO_FPS = 15
LOBBY_FPS = 5
WINDOW_CAPTION_SERVER = "Tank Wars - Code Challenge"
WINDOW_CAPTION_CLIENT = 'Tank Wars - "Headless" Client'

# ---------------------------------------------------------------------------
# Game Rules
# ---------------------------------------------------------------------------
GAME_TIMEOUT_SECS = 4 * 60  # 4 minutes
INTRO_DISPLAY_SECS = 1  # seconds to show the intro screen (use 5 for prod)

# ---------------------------------------------------------------------------
# Tank Properties
# ---------------------------------------------------------------------------
TANK_WIDTH = 56
TANK_HEIGHT = 40
TANK_IMAGE_SIZE = (TANK_WIDTH, TANK_HEIGHT)
TANK_START_HEALTH = 200
TANK_TURN_SPEED = math.radians(7.5)
TANK_TURRET_TURN_SPEED = math.radians(20)
TANK_MAX_SPEED = 3.5

# Health bar drawn above each tank
TANK_HEALTH_BAR_OFFSET_Y = -40
TANK_HEALTH_BAR_SIZE = (50, 5)

# ---------------------------------------------------------------------------
# Shot Properties
# ---------------------------------------------------------------------------
SHOT_IMAGE_SIZE = (20, 8)
TURRET_IMAGE_SIZE = (80, 19)
SHOT_SPEED = 15.0
SHOT_COOLDOWN_SECS = 5  # seconds between shots
MAX_SHOT_DAMAGE = 100
DAMAGE_DIVISOR = 60  # divisor in damage-falloff calculation

# Explosion durations (in seconds) for different events
EXPLOSION_DURATION_BORDER = 0.5
EXPLOSION_DURATION_HIT = 0.75

# ---------------------------------------------------------------------------
# Explosion Animation
# ---------------------------------------------------------------------------
EXPLOSION_MAX_RADIUS = 50
EXPLOSION_NUM_CIRCLES = 5
EXPLOSION_COLOR_RED = 255
EXPLOSION_COLOR_GREEN_MIN = 100
EXPLOSION_COLOR_GREEN_MAX = 160
EXPLOSION_COLOR_BLUE = 0

# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------
DEFAULT_SERVER_IP = "localhost"
DEFAULT_SERVER_PORT = 49909
SOCKET_BUFFER_SIZE = 4 * 1024  # 4 KiB
CONNECTION_TIMEOUT_SECS = 5

# ---------------------------------------------------------------------------
# Colors (RGB tuples)
# ---------------------------------------------------------------------------
COLOR_WHEAT = (245, 222, 179)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GREY = (110, 110, 110)
COLOR_BLUE = (0, 0, 255)

COLOR_RED = (200, 0, 0)
COLOR_LIGHT_RED = (255, 0, 0)

COLOR_YELLOW = (200, 200, 0)
COLOR_LIGHT_YELLOW = (255, 255, 0)

COLOR_GREEN = (34, 177, 76)
COLOR_LIGHT_GREEN = (0, 255, 0)

COLOR_HEALTH_GREEN = (0, 255, 0)
COLOR_HEALTH_RED = (255, 0, 0)

COLOR_CLIENT_TEXT = (200, 200, 200)

# Mapping from team name to display color
COLOR_LOOKUP = {
    "red": COLOR_RED,
    "blue": COLOR_BLUE,
    "green": COLOR_GREEN,
    "yellow": COLOR_YELLOW,
}

# ---------------------------------------------------------------------------
# Starting Positions
# ---------------------------------------------------------------------------
# Each entry: (position_x, position_y, direction_x, direction_y)
# Positions are defined as offsets from display edges (50px margin).
_MARGIN = 50
STARTING_POSITIONS = {
    "red":    {"pos": (_MARGIN, _MARGIN),
               "dir": (-1, -1)},                                # upper-left
    "blue":   {"pos": (DISPLAY_WIDTH - _MARGIN, _MARGIN),
               "dir": (1, -1)},                                 # upper-right
    "yellow": {"pos": (_MARGIN, DISPLAY_HEIGHT - _MARGIN),
               "dir": (-1, 1)},                                 # lower-left
    "green":  {"pos": (DISPLAY_WIDTH - _MARGIN, DISPLAY_HEIGHT - _MARGIN),
               "dir": (1, 1)},                                  # lower-right
}

STARTING_POSITION_NAMES = ["red", "blue", "yellow", "green"]

# ---------------------------------------------------------------------------
# Font Configuration
# ---------------------------------------------------------------------------
FONT_NAME = "Arial"
FONT_SIZE_VSMALL = 18
FONT_SIZE_SMALL = 25
FONT_SIZE_MEDIUM = 50
FONT_SIZE_LARGE = 85

# ---------------------------------------------------------------------------
# Screens / UI Layout
# ---------------------------------------------------------------------------
LOBBY_TEXT_TOPLEFT = (300, 150)
LOBBY_LINE_HEIGHT = 100
LINES_PRINT_TOPLEFT = (50, 50)
LINES_PRINT_LINE_HEIGHT = 60
TIMER_POSITION = (5, 5)

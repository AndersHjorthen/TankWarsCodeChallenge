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

# ---------------------------------------------------------------------------
# Arena Obstacles
# ---------------------------------------------------------------------------
# Default arena obstacles - list of (x, y, width, height)
ARENA_OBSTACLES = [
    (500, 300, 200, 20),   # horizontal wall center-top
    (500, 480, 200, 20),   # horizontal wall center-bottom
    (350, 350, 20, 100),   # vertical wall left
    (830, 350, 20, 100),   # vertical wall right
]

OBSTACLE_COLOR = (130, 130, 130)
OBSTACLE_BORDER_COLOR = (90, 90, 90)

# ---------------------------------------------------------------------------
# Power-ups
# ---------------------------------------------------------------------------
POWERUP_SPAWN_INTERVAL = 15    # seconds between spawns
POWERUP_DURATION = 10          # seconds a power-up effect lasts
POWERUP_SPEED_MULTIPLIER = 1.5
POWERUP_RAPID_FIRE_COOLDOWN = 1  # seconds (vs normal SHOT_COOLDOWN_SECS)
POWERUP_SHIELD_DAMAGE_REDUCTION = 0.5
POWERUP_RADIUS = 15            # visual radius for rendering
POWERUP_PICKUP_RADIUS = 30     # collision radius for pickup

POWERUP_COLORS = {
    "speed_boost": (0, 120, 255),    # blue
    "rapid_fire": (255, 50, 50),     # red
    "shield": (50, 255, 50),         # green
}

POWERUP_LABELS = {
    "speed_boost": "S",
    "rapid_fire": "R",
    "shield": "D",
}

# ---------------------------------------------------------------------------
# Arena Renderer
# ---------------------------------------------------------------------------
ARENA_BG_COLOR = (30, 35, 45)            # dark blue-grey background
ARENA_GRID_COLOR = (40, 46, 58)          # subtle grid lines
ARENA_GRID_SPACING = 60                  # pixels between grid lines
ARENA_BORDER_COLOR_OUTER = (80, 90, 110) # outer border line
ARENA_BORDER_COLOR_INNER = (60, 70, 85)  # inner border line
ARENA_BORDER_WIDTH = 3                   # thickness of each border line
ARENA_BORDER_GAP = 6                     # gap between double lines
ARENA_CORNER_ACCENT_LEN = 30            # length of corner accent marks
ARENA_CORNER_ACCENT_COLOR = (100, 120, 150)

# ---------------------------------------------------------------------------
# Particle System
# ---------------------------------------------------------------------------
PARTICLE_MAX_COUNT = 500
PARTICLE_DEFAULT_SIZE = 3.0
PARTICLE_MIN_SIZE = 0.5                  # particles below this are removed

# Smoke trail particles (behind moving tanks)
SMOKE_TRAIL_RATE = 2                     # particles per frame while moving
SMOKE_TRAIL_SIZE = 4.0
SMOKE_TRAIL_LIFETIME = 0.6              # seconds
SMOKE_TRAIL_SPEED = 0.5
SMOKE_TRAIL_COLOR = (80, 80, 90)
SMOKE_TRAIL_COLOR_VAR = 20              # random variation in RGB

# Shot tracer particles
TRACER_RATE = 3                          # particles per frame along shot path
TRACER_SIZE = 2.5
TRACER_LIFETIME = 0.3
TRACER_SPEED = 0.3
TRACER_COLOR = (255, 200, 80)
TRACER_COLOR_VAR = 30

# Muzzle flash
MUZZLE_FLASH_PARTICLES = 8
MUZZLE_FLASH_SIZE = 5.0
MUZZLE_FLASH_LIFETIME = 0.15
MUZZLE_FLASH_SPEED = 4.0
MUZZLE_FLASH_COLOR = (255, 240, 150)

# Explosion particles (replaces old Explosion class)
EXPLOSION_PARTICLE_COUNT = 30
EXPLOSION_PARTICLE_SIZE = 5.0
EXPLOSION_PARTICLE_LIFETIME = 0.8
EXPLOSION_PARTICLE_SPEED = 5.0
EXPLOSION_FIRE_COLORS = [
    (255, 100, 20),
    (255, 160, 40),
    (255, 200, 60),
    (255, 80, 10),
]

# Debris chunks in explosions
DEBRIS_PARTICLE_COUNT = 8
DEBRIS_PARTICLE_SIZE = 3.0
DEBRIS_PARTICLE_LIFETIME = 1.0
DEBRIS_PARTICLE_SPEED = 3.5
DEBRIS_COLOR = (140, 140, 130)
DEBRIS_COLOR_VAR = 30

# ---------------------------------------------------------------------------
# Effects
# ---------------------------------------------------------------------------
# Hit flash (brief white overlay on damaged tank)
HIT_FLASH_DURATION = 0.1                # seconds

# Screen shake on tank destruction
SCREEN_SHAKE_DURATION = 0.4             # seconds
SCREEN_SHAKE_INTENSITY = 8              # max pixel offset

# Shot glow (additive circle behind shot sprite)
SHOT_GLOW_RADIUS = 12
SHOT_GLOW_COLOR = (255, 180, 60)
SHOT_GLOW_ALPHA = 60

# Power-up aura ring around affected tanks
AURA_RING_RADIUS = 35
AURA_RING_WIDTH = 2
AURA_RING_ALPHA = 120
AURA_PULSE_SPEED = 3.0                  # Hz

# ---------------------------------------------------------------------------
# HUD
# ---------------------------------------------------------------------------
HUD_SCOREBOARD_POS = (10, 10)           # top-left corner
HUD_SCOREBOARD_WIDTH = 200
HUD_SCOREBOARD_LINE_HEIGHT = 22
HUD_SCOREBOARD_BG_ALPHA = 140
HUD_SCOREBOARD_BG_COLOR = (20, 20, 30)

HUD_TIMER_COLOR_NORMAL = (180, 180, 190)
HUD_TIMER_COLOR_WARNING = (255, 200, 50)  # < 60s
HUD_TIMER_COLOR_CRITICAL = (255, 60, 60)  # < 15s
HUD_TIMER_WARNING_SECS = 60
HUD_TIMER_CRITICAL_SECS = 15

HUD_KILLFEED_POS = (10, 10)             # offset from top-right
HUD_KILLFEED_MAX_ENTRIES = 5
HUD_KILLFEED_DISPLAY_SECS = 5.0
HUD_KILLFEED_LINE_HEIGHT = 20
HUD_KILLFEED_BG_ALPHA = 140

# ---------------------------------------------------------------------------
# Obstacle Visuals (textured)
# ---------------------------------------------------------------------------
OBSTACLE_FILL_COLOR = (70, 75, 85)
OBSTACLE_HASH_COLOR = (55, 60, 70)
OBSTACLE_HASH_SPACING = 8               # pixels between hash lines
OBSTACLE_HIGHLIGHT_COLOR = (90, 95, 110) # top/left edge highlight
OBSTACLE_SHADOW_COLOR = (45, 48, 55)     # bottom/right edge shadow
OBSTACLE_BORDER_WIDTH_NEW = 2

# ---------------------------------------------------------------------------
# Health Bar (enhanced)
# ---------------------------------------------------------------------------
HEALTH_BAR_BORDER_COLOR = (30, 30, 30)
HEALTH_BAR_BORDER_WIDTH = 1
HEALTH_BAR_NAME_OFFSET_Y = 8            # pixels below health bar to show name
HEALTH_BAR_NAME_FONT_SIZE = 12

# ---------------------------------------------------------------------------
# Screen styling
# ---------------------------------------------------------------------------
SCREEN_TEXT_SHADOW_OFFSET = 2
SCREEN_TEXT_SHADOW_COLOR = (0, 0, 0)
LOBBY_PANEL_BG_COLOR = (20, 25, 35)
LOBBY_PANEL_BG_ALPHA = 180
LOBBY_PANEL_PADDING = 20
LOBBY_COLOR_INDICATOR_SIZE = 16         # square color swatch size
GAMEOVER_WINNER_HIGHLIGHT_COLOR = (255, 215, 0)  # gold
GAMEOVER_STATS_BG_ALPHA = 160

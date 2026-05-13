import os

WIDTH  = 480
HEIGHT = 720
FPS    = 60
TITLE  = "VOID"

PLAY_TOP    = 55   # HUD bar height at top
PLAY_BOTTOM = HEIGHT - 90  # dialogue bar at bottom (used only during active dialogue)

# Colors
BLACK      = (5, 5, 15)
NEAR_BLACK = (10, 10, 25)
WHITE      = (255, 255, 255)
GRAY       = (120, 120, 140)
DIM_GRAY   = (55, 55, 75)
CYAN       = (0, 220, 255)
RED        = (255, 60, 60)
DARK_RED   = (180, 20, 20)
ORANGE     = (255, 150, 0)
YELLOW     = (255, 220, 50)
GREEN      = (80, 255, 120)
PURPLE     = (200, 60, 255)
PINK       = (255, 100, 200)
BLUE       = (80, 120, 255)
TEAL       = (0, 200, 180)

# Player
PLAYER_SPEED        = 5
PLAYER_FOCUS_SPEED  = 2
PLAYER_HITBOX_R     = 3
PLAYER_LIVES        = 3
PLAYER_INVINCIBLE   = 120
PLAYER_SHOOT_FRAMES = [10, 8, 6, 5, 4]   # frames between shots per tier 0-4

# Power pickups
POWER_DROP_CHANCE       = 0.22
POWER_PER_CRYSTAL       = 8
POWER_TIER_THRESHOLDS   = [0, 25, 60, 110, 170]

# Enemy bullets
BULLET_BASE_SPEED  = 3.5
BULLET_SPEED_SCALE = 0.06

# Graze
GRAZE_RADIUS = 14

# Scoring
SCORE_SCOUT   = 100
SCORE_ZIGZAG  = 150
SCORE_HOVER   = 300
SCORE_TANK    = 500
SCORE_SWARMER = 50
SCORE_BOSS_PHASE = 2000
SCORE_GRAZE   = 5

# Wave
BOSS_EVERY = 5

# Persistence
SAVE_PATH = os.path.expanduser("~/.bullet-hell-save.json")

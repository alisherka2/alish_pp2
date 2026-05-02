# config.py — shared constants for the Snake TSIS4 project

CELL     = 20
COLS     = 30
ROWS     = 28
SCREEN_W = COLS * CELL          # 600
SCREEN_H = ROWS * CELL + 50     # 610
HUD_H    = 50
BASE_FPS = 10

UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)

# ── Colours ──────────────────────────────────────────────────────────────────
BLACK       = (  0,   0,   0)
WHITE       = (255, 255, 255)
BG          = ( 30,  30,  30)
GRID_LINE   = ( 45,  45,  45)
SNAKE_HEAD  = (  0, 210,  80)
SNAKE_BODY  = (  0, 160,  60)
SNAKE_EYE   = (255, 255, 255)
RED         = (220,  50,  50)
YELLOW      = (255, 220,   0)
ORANGE      = (255, 140,   0)
PURPLE      = (180,  60, 200)
SILVER      = (192, 192, 192)
DARK_RED    = (140,   0,   0)   # poison food
CYAN        = (  0, 220, 220)   # speed boost
LIME        = (180, 255,   0)   # slow motion
GOLD        = (255, 200,   0)   # shield
OBSTACLE    = ( 90,  90,  90)   # obstacle wall block
DARK_BG     = ( 15,  15,  15)
PANEL       = ( 25,  25,  35)
ACCENT      = (  0, 180, 255)

# ── Food definitions ──────────────────────────────────────────────────────────
FOOD_TYPES = [
    {"label": "Apple",  "value": 1, "colour": RED,    "weight": 50, "lifetime": None},
    {"label": "Orange", "value": 2, "colour": ORANGE, "weight": 30, "lifetime": 50},
    {"label": "Grape",  "value": 3, "colour": PURPLE, "weight": 15, "lifetime": 30},
    {"label": "Star",   "value": 5, "colour": YELLOW, "weight": 5,  "lifetime": 20},
]

MAX_FOOD_ON_SCREEN   = 4
FOOD_SPAWN_INTERVAL  = 15   # frames between spawn attempts

# ── Power-up definitions ──────────────────────────────────────────────────────
POWERUP_FIELD_TIMEOUT_MS = 8_000   # ms before uncollected power-up vanishes
POWERUP_EFFECT_MS        = 5_000   # ms the effect lasts once collected

POWERUP_TYPES = [
    {"label": "Speed Boost",  "colour": CYAN,  "kind": "speed"},
    {"label": "Slow Motion",  "colour": LIME,  "kind": "slow"},
    {"label": "Shield",       "colour": GOLD,  "kind": "shield"},
]

POWERUP_SPAWN_INTERVAL = 200  # frames between spawn attempts for power-ups
OBSTACLE_COUNT_PER_LEVEL = 5  # new obstacle blocks added each level (from lvl3)
LEVEL_FOOD_THRESHOLD = 5      # food items to eat before levelling up

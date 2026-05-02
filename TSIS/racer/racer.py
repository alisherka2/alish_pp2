"""
racer.py  –  TSIS 3
All game-world classes:
  Road, PlayerCar, EnemyCar, Obstacle (oil / barrier / speedbump / nitrostrip),
  Coin (weighted, from Practice 11), PowerUp (Nitro / Shield / Repair)
"""
import pygame
import random
import math

# ── layout ──────────────────────────────────────────────────────
SCREEN_W   = 400
SCREEN_H   = 600
ROAD_LEFT  = 60
ROAD_RIGHT = 340
LANE_W     = (ROAD_RIGHT - ROAD_LEFT) // 3   # 93 px

# ── colours ─────────────────────────────────────────────────────
WHITE   = (255, 255, 255)
BLACK   = (0,   0,   0  )
GRAY    = (90,  90,  90 )
DKGRAY  = (50,  50,  50 )
RED     = (210, 30,  30 )
LT_BLU  = (160, 210, 255)
GRASS   = (35,  105, 35 )
YELLOW  = (255, 220,   0)
ORANGE  = (255, 130,   0)
CYAN    = (0,   200, 220)
GREEN   = (50,  200,  70)

BRONZE_COL  = (205, 127,  50)
SILVER_COL  = (192, 192, 192)
GOLD_COL    = (255, 215,   0)
DIAMOND_COL = (185, 242, 255)

# ── coin definitions ────────────────────────────────────────────
COIN_TYPES = [
    {"label": "B", "value":  1, "colour": BRONZE_COL,  "weight": 50, "radius": 10},
    {"label": "S", "value":  3, "colour": SILVER_COL,  "weight": 30, "radius": 11},
    {"label": "G", "value":  5, "colour": GOLD_COL,    "weight": 15, "radius": 12},
    {"label": "D", "value": 10, "colour": DIAMOND_COL, "weight":  5, "radius": 13},
]

COINS_PER_BOOST = 5
SPEED_BOOST     = 1


# ════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════

def lane_center_x(lane: int, obj_w: int) -> int:
    return ROAD_LEFT + lane * LANE_W + (LANE_W - obj_w) // 2

def random_lane_x(obj_w: int) -> int:
    return lane_center_x(random.randint(0, 2), obj_w)

def weighted_choice(options):
    total, roll, running = sum(o["weight"] for o in options), random.randint(1, sum(o["weight"] for o in options)), 0
    for opt in options:
        running += opt["weight"]
        if roll <= running:
            return opt
    return options[-1]


# ════════════════════════════════════════════════════════════════
#  ROAD
# ════════════════════════════════════════════════════════════════

class Road:
    LINE_H   = 55
    LINE_GAP = 35
    SEGMENT  = LINE_H + LINE_GAP

    def __init__(self):
        self.offset = 0
        self.speed  = 5

    def update(self):
        self.offset = (self.offset + self.speed) % self.SEGMENT

    def draw(self, surface):
        surface.fill(GRASS)
        pygame.draw.rect(surface, GRAY, (ROAD_LEFT, 0, ROAD_RIGHT - ROAD_LEFT, SCREEN_H))
        pygame.draw.rect(surface, WHITE, (ROAD_LEFT - 4, 0, 4, SCREEN_H))
        pygame.draw.rect(surface, WHITE, (ROAD_RIGHT,    0, 4, SCREEN_H))
        for lane_idx in range(1, 3):
            x = ROAD_LEFT + LANE_W * lane_idx - 2
            y = self.offset - self.SEGMENT
            while y < SCREEN_H:
                pygame.draw.rect(surface, WHITE, (x, y, 4, self.LINE_H))
                y += self.SEGMENT


# ════════════════════════════════════════════════════════════════
#  PLAYER CAR
# ════════════════════════════════════════════════════════════════

class PlayerCar:
    W, H = 38, 68

    def __init__(self, color=(30, 90, 210)):
        self.x     = SCREEN_W // 2 - self.W // 2
        self.y     = SCREEN_H - 110
        self.spd   = 5
        self.color = color

    def draw(self, surface, shield_active=False):
        x, y, w, h = self.x, self.y, self.W, self.H
        if shield_active:
            pygame.draw.ellipse(surface, CYAN,
                                (x - 6, y - 6, w + 12, h + 12), 3)
        pygame.draw.rect(surface, self.color,  (x, y, w, h), border_radius=6)
        pygame.draw.rect(surface, LT_BLU, (x+5, y+8,    w-10, 18))
        pygame.draw.rect(surface, LT_BLU, (x+5, y+h-22, w-10, 12))
        for wx, wy in [(x-6,y+6),(x+w-2,y+6),(x-6,y+h-22),(x+w-2,y+h-22)]:
            pygame.draw.rect(surface, BLACK, (wx, wy, 8, 14), border_radius=2)

    def move(self, keys, nitro_active=False):
        spd = self.spd * (1.6 if nitro_active else 1.0)
        if keys[pygame.K_LEFT]  and self.x > ROAD_LEFT:            self.x -= spd
        if keys[pygame.K_RIGHT] and self.x + self.W < ROAD_RIGHT:  self.x += spd
        if keys[pygame.K_UP]    and self.y > 0:                    self.y -= spd
        if keys[pygame.K_DOWN]  and self.y + self.H < SCREEN_H:    self.y += spd

    def rect(self):
        return pygame.Rect(self.x + 4, self.y + 4, self.W - 8, self.H - 8)


# ════════════════════════════════════════════════════════════════
#  ENEMY CAR
# ════════════════════════════════════════════════════════════════

class EnemyCar:
    W, H = 38, 68

    def __init__(self, speed, player_x=None):
        # safe spawn: pick lane different from player's if possible
        lanes = [0, 1, 2]
        if player_x is not None:
            player_lane = (player_x - ROAD_LEFT) // LANE_W
            player_lane = max(0, min(2, player_lane))
            other = [l for l in lanes if l != player_lane]
            lane  = random.choice(other if other else lanes)
        else:
            lane = random.randint(0, 2)
        self.x   = lane_center_x(lane, self.W)
        self.y   = -self.H - random.randint(0, 60)
        self.spd = speed
        self.col = random.choice([(200,40,40),(180,90,0),(140,0,140),(30,130,180)])

    def draw(self, surface):
        x, y, w, h = self.x, self.y, self.W, self.H
        pygame.draw.rect(surface, self.col, (x,y,w,h), border_radius=6)
        pygame.draw.rect(surface, LT_BLU, (x+5,y+h-22,w-10,12))
        for wx, wy in [(x-6,y+6),(x+w-2,y+6),(x-6,y+h-22),(x+w-2,y+h-22)]:
            pygame.draw.rect(surface, BLACK, (wx, wy, 8, 14), border_radius=2)

    def update(self, slow=False):
        self.y += self.spd * (0.4 if slow else 1.0)

    def off_screen(self):
        return self.y > SCREEN_H

    def rect(self):
        return pygame.Rect(self.x+4, self.y+4, self.W-8, self.H-8)


# ════════════════════════════════════════════════════════════════
#  OBSTACLE
# ════════════════════════════════════════════════════════════════

class Obstacle:
    """
    Types:
      oil      – slows the player (no crash), drawn as dark ellipse
      barrier  – solid crash (ends run unless shielded)
      bump     – speed bump, visual only (harmless)
      nitro    – green strip: boosts road speed briefly
    """
    KINDS = ["oil", "barrier", "bump", "nitro"]

    def __init__(self, speed):
        self.kind = random.choice(self.KINDS)
        w = 60 if self.kind in ("barrier", "nitro") else 50
        self.w    = w
        self.h    = 18 if self.kind != "barrier" else 22
        self.x    = random_lane_x(w)
        self.y    = -self.h
        self.spd  = speed

    def draw(self, surface):
        x, y, w, h = self.x, self.y, self.w, self.h
        if self.kind == "oil":
            pygame.draw.ellipse(surface, (20, 20, 20), (x, y, w, h))
            pygame.draw.ellipse(surface, (60, 60, 80), (x+4, y+3, w-8, h-6))
        elif self.kind == "barrier":
            pygame.draw.rect(surface, ORANGE, (x, y, w, h), border_radius=4)
            pygame.draw.rect(surface, (255,80,0), (x+4, y+4, w-8, h-8), border_radius=3)
            label = pygame.font.SysFont("Arial", 11, bold=True).render("BARRIER", True, WHITE)
            surface.blit(label, label.get_rect(center=(x+w//2, y+h//2)))
        elif self.kind == "bump":
            pygame.draw.rect(surface, (80, 50, 20), (x, y+h//2, w, h//2), border_radius=3)
            for i in range(0, w, 12):
                pygame.draw.rect(surface, YELLOW, (x+i, y+h//2, 6, h//2), border_radius=2)
        elif self.kind == "nitro":
            pygame.draw.rect(surface, (0, 200, 80), (x, y, w, h), border_radius=4)
            label = pygame.font.SysFont("Arial", 11, bold=True).render("NITRO!", True, WHITE)
            surface.blit(label, label.get_rect(center=(x+w//2, y+h//2)))

    def update(self):
        self.y += self.spd

    def off_screen(self):
        return self.y > SCREEN_H

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)


# ════════════════════════════════════════════════════════════════
#  COIN  (unchanged from Practice 11)
# ════════════════════════════════════════════════════════════════

class Coin:
    def __init__(self, speed):
        tier        = weighted_choice(COIN_TYPES)
        self.label  = tier["label"]
        self.value  = tier["value"]
        self.colour = tier["colour"]
        self.R      = tier["radius"]
        self.x      = random.randint(ROAD_LEFT + self.R + 2, ROAD_RIGHT - self.R - 2)
        self.y      = -self.R
        self.spd    = speed
        self._small = pygame.font.SysFont("Arial", 13, bold=True)

    def draw(self, surface):
        r, g, b  = self.colour
        dark_col = (max(0,r-60), max(0,g-60), max(0,b-60))
        pygame.draw.circle(surface, self.colour, (self.x, self.y), self.R)
        pygame.draw.circle(surface, dark_col,    (self.x, self.y), self.R, 2)
        lbl = self._small.render(self.label, True, dark_col)
        surface.blit(lbl, lbl.get_rect(center=(self.x, self.y)))

    def update(self):
        self.y += self.spd

    def off_screen(self):
        return self.y - self.R > SCREEN_H

    def rect(self):
        return pygame.Rect(self.x-self.R, self.y-self.R, self.R*2, self.R*2)


# ════════════════════════════════════════════════════════════════
#  POWER-UP
# ════════════════════════════════════════════════════════════════

class PowerUp:
    KINDS = [
        {"name": "nitro",  "color": (255, 140,  0), "symbol": "N", "duration": 4.0},
        {"name": "shield", "color": (0,   200, 220), "symbol": "S", "duration": 0},   # until hit
        {"name": "repair", "color": (80,  220,  80), "symbol": "R", "duration": 0},   # instant
    ]
    W = H = 28
    LIFETIME = 8.0   # seconds before auto-despawn

    def __init__(self, speed):
        kind       = random.choice(self.KINDS)
        self.name  = kind["name"]
        self.color = kind["color"]
        self.sym   = kind["symbol"]
        self.dur   = kind["duration"]
        self.x     = random_lane_x(self.W)
        self.y     = -self.H
        self.spd   = speed
        self.age   = 0.0
        self._font = pygame.font.SysFont("Arial", 14, bold=True)

    def draw(self, surface):
        x, y, w, h = self.x, self.y, self.W, self.H
        pygame.draw.rect(surface, self.color, (x, y, w, h), border_radius=6)
        pygame.draw.rect(surface, WHITE,      (x, y, w, h), 2, border_radius=6)
        lbl = self._font.render(self.sym, True, WHITE)
        surface.blit(lbl, lbl.get_rect(center=(x+w//2, y+h//2)))

    def update(self, dt):
        self.y   += self.spd
        self.age += dt

    def off_screen(self):
        return self.y > SCREEN_H or self.age >= self.LIFETIME

    def rect(self):
        return pygame.Rect(self.x, self.y, self.W, self.H)

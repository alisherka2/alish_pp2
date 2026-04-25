import pygame
import random
import sys

pygame.init()

# ══════════════════════════════════════════════════════════════
#  SCREEN & ROAD CONSTANTS
# ══════════════════════════════════════════════════════════════
SCREEN_W, SCREEN_H = 400, 600
FPS = 60

# The tarmac strip sits between x=60 and x=340
ROAD_LEFT  = 60
ROAD_RIGHT = 340
LANE_W     = (ROAD_RIGHT - ROAD_LEFT) // 3   # 3 equal lanes → 93 px each

# ══════════════════════════════════════════════════════════════
#  COLOUR PALETTE
# ══════════════════════════════════════════════════════════════
WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0  )
GRAY   = (90,  90,  90 )
DKGRAY = (50,  50,  50 )
RED    = (210, 30,  30 )
BLUE   = (30,  90,  210)
LT_BLU = (160, 210, 255)
GRASS  = (45,  120, 45 )

# Coin colours (one per tier)
BRONZE_COL  = (205, 127,  50)   # bronze
SILVER_COL  = (192, 192, 192)   # silver
GOLD_COL    = (255, 215,   0)   # gold
DIAMOND_COL = (185, 242, 255)   # diamond / cyan-white

# HUD text colours
HUD_GREEN  = (80,  220,  80)
HUD_ORANGE = (255, 160,   0)

# ══════════════════════════════════════════════════════════════
#  COIN TYPE DEFINITIONS
#  Each dict describes one coin tier:
#    label   – displayed on the coin
#    value   – score points when collected
#    colour  – RGB fill colour
#    weight  – relative spawn probability (higher = more common)
#    radius  – pixel radius of the drawn circle
# ══════════════════════════════════════════════════════════════
COIN_TYPES = [
    {"label": "B", "value": 1, "colour": BRONZE_COL,  "weight": 50, "radius": 10},
    {"label": "S", "value": 3, "colour": SILVER_COL,  "weight": 30, "radius": 11},
    {"label": "G", "value": 5, "colour": GOLD_COL,    "weight": 15, "radius": 12},
    {"label": "D", "value": 10,"colour": DIAMOND_COL, "weight": 5,  "radius": 13},
]

# ── Speed boost settings ──────────────────────────────────────
# Enemy speed increases by SPEED_BOOST every COINS_PER_BOOST coins collected.
COINS_PER_BOOST = 5    # collect this many coins → enemies get faster
SPEED_BOOST     = 1    # how much faster each time

# ══════════════════════════════════════════════════════════════
#  PYGAME SETUP
# ══════════════════════════════════════════════════════════════
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Racer – Practice 11")
clock = pygame.time.Clock()
font  = pygame.font.SysFont("Arial", 22, bold=True)
big   = pygame.font.SysFont("Arial", 48, bold=True)
small = pygame.font.SysFont("Arial", 13, bold=True)


# ══════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════

def random_lane_x(obj_width: int) -> int:
    """
    Pick one of the 3 lanes at random and return the left-edge X
    that centres `obj_width` inside that lane.
    """
    lane = random.randint(0, 2)
    return ROAD_LEFT + lane * LANE_W + (LANE_W - obj_width) // 2


def weighted_choice(options: list) -> dict:
    """
    Select a random item from `options` list using each item's 'weight'.
    Higher weight = higher probability of being chosen.

    Example: weights [50, 30, 15, 5] → total 100
    A roll of 1-50 picks index 0, 51-80 picks index 1, etc.
    """
    total   = sum(o["weight"] for o in options)
    roll    = random.randint(1, total)
    running = 0
    for opt in options:
        running += opt["weight"]
        if roll <= running:
            return opt
    return options[-1]   # fallback (should never reach here)


# ══════════════════════════════════════════════════════════════
#  ROAD CLASS  –  scrolling tarmac with animated lane markings
# ══════════════════════════════════════════════════════════════
class Road:
    LINE_H   = 55    # length of one dashed-line segment (px)
    LINE_GAP = 35    # gap between segments
    SEGMENT  = LINE_H + LINE_GAP   # full cycle height

    def __init__(self):
        self.offset = 0    # current vertical scroll position
        self.speed  = 5    # scrolling speed (pixels per frame)

    def update(self):
        """Advance the scroll animation by one frame."""
        self.offset = (self.offset + self.speed) % self.SEGMENT

    def draw(self, surface):
        """Paint grass, tarmac, edge lines, and dashed lane dividers."""
        # Green grass on both sides of the road
        surface.fill(GRASS)

        # Tarmac strip
        pygame.draw.rect(surface, GRAY,
                         (ROAD_LEFT, 0, ROAD_RIGHT - ROAD_LEFT, SCREEN_H))

        # White edge borders
        pygame.draw.rect(surface, WHITE, (ROAD_LEFT - 4, 0, 4, SCREEN_H))
        pygame.draw.rect(surface, WHITE, (ROAD_RIGHT,    0, 4, SCREEN_H))

        # Two interior dashed dividers (for 3 lanes)
        for lane_idx in range(1, 3):
            x = ROAD_LEFT + LANE_W * lane_idx - 2
            # Start one full segment above the screen to prevent a gap at top
            y = self.offset - self.SEGMENT
            while y < SCREEN_H:
                pygame.draw.rect(surface, WHITE, (x, y, 4, self.LINE_H))
                y += self.SEGMENT


# ══════════════════════════════════════════════════════════════
#  PLAYER CAR CLASS
# ══════════════════════════════════════════════════════════════
class PlayerCar:
    W, H = 38, 68   # car width and height in pixels

    def __init__(self):
        # Start horizontally centred, near the bottom of the screen
        self.x   = SCREEN_W // 2 - self.W // 2
        self.y   = SCREEN_H - 110
        self.spd = 5    # movement speed (px per frame)

    def draw(self, surface):
        """Draw a simple top-down car with body, windows, and wheels."""
        x, y, w, h = self.x, self.y, self.W, self.H

        # Car body (blue rectangle with rounded corners)
        pygame.draw.rect(surface, BLUE,   (x, y, w, h), border_radius=6)

        # Windshield and rear window (light-blue rectangles)
        pygame.draw.rect(surface, LT_BLU, (x + 5,  y + 8,    w - 10, 18))
        pygame.draw.rect(surface, LT_BLU, (x + 5,  y + h-22, w - 10, 12))

        # Four wheels (black rectangles at each corner)
        for wx, wy in [(x-6, y+6), (x+w-2, y+6),
                       (x-6, y+h-22), (x+w-2, y+h-22)]:
            pygame.draw.rect(surface, BLACK, (wx, wy, 8, 14), border_radius=2)

    def move(self, keys):
        """
        Move the player car based on currently held arrow keys.
        Clamps position to the road boundaries / screen edges.
        """
        if keys[pygame.K_LEFT]  and self.x > ROAD_LEFT:              self.x -= self.spd
        if keys[pygame.K_RIGHT] and self.x + self.W < ROAD_RIGHT:    self.x += self.spd
        if keys[pygame.K_UP]    and self.y > 0:                      self.y -= self.spd
        if keys[pygame.K_DOWN]  and self.y + self.H < SCREEN_H:      self.y += self.spd

    def rect(self) -> pygame.Rect:
        """Return a slightly-shrunk collision rectangle (feels fairer to the player)."""
        return pygame.Rect(self.x + 4, self.y + 4, self.W - 8, self.H - 8)


# ══════════════════════════════════════════════════════════════
#  ENEMY CAR CLASS
# ══════════════════════════════════════════════════════════════
class EnemyCar:
    W, H = 38, 68

    def __init__(self, speed: int):
        """
        Spawn above the screen in a random lane.
        `speed` – downward movement speed (px per frame), passed from game loop.
        """
        self.x   = random_lane_x(self.W)
        self.y   = -self.H - random.randint(0, 60)   # start above the visible area
        self.spd = speed
        # Each enemy gets a random colour for visual variety
        self.col = random.choice([
            (200, 40,  40),   # red
            (180, 90,   0),   # orange
            (140,  0, 140),   # purple
        ])

    def draw(self, surface):
        """Draw enemy car facing towards the player (windshield at bottom)."""
        x, y, w, h = self.x, self.y, self.W, self.H
        pygame.draw.rect(surface, self.col, (x, y, w, h), border_radius=6)
        pygame.draw.rect(surface, LT_BLU, (x+5, y+h-22, w-10, 12))   # windshield
        for wx, wy in [(x-6, y+6), (x+w-2, y+6),
                       (x-6, y+h-22), (x+w-2, y+h-22)]:
            pygame.draw.rect(surface, BLACK, (wx, wy, 8, 14), border_radius=2)

    def update(self):
        """Move the car downward."""
        self.y += self.spd

    def off_screen(self) -> bool:
        """True when the car has scrolled past the bottom of the screen."""
        return self.y > SCREEN_H

    def rect(self) -> pygame.Rect:
        """Shrunk collision rectangle for the enemy car."""
        return pygame.Rect(self.x + 4, self.y + 4, self.W - 8, self.H - 8)


# ══════════════════════════════════════════════════════════════
#  COIN CLASS  –  weighted random tiers
# ══════════════════════════════════════════════════════════════
class Coin:
    def __init__(self, speed: int):
        """
        Pick a random coin tier via weighted_choice(), then spawn at the
        top of the screen in a random horizontal position within the road.
        """
        # Select tier (Bronze / Silver / Gold / Diamond)
        tier       = weighted_choice(COIN_TYPES)
        self.label  = tier["label"]
        self.value  = tier["value"]
        self.colour = tier["colour"]
        self.R      = tier["radius"]      # radius for drawing

        # Random X within the road (ensuring the circle stays inside)
        self.x   = random.randint(ROAD_LEFT + self.R + 2,
                                  ROAD_RIGHT - self.R - 2)
        self.y   = -self.R               # start just above screen
        self.spd = speed

    def draw(self, surface):
        """Draw coin as a filled circle with a darker border and the tier letter."""
        # Darker version of the coin colour for the ring
        r, g, b  = self.colour
        dark_col = (max(0, r - 60), max(0, g - 60), max(0, b - 60))

        pygame.draw.circle(surface, self.colour, (self.x, self.y), self.R)
        pygame.draw.circle(surface, dark_col,    (self.x, self.y), self.R, 2)

        # Print the tier label centred on the coin
        lbl = small.render(self.label, True, dark_col)
        surface.blit(lbl, lbl.get_rect(center=(self.x, self.y)))

    def update(self):
        """Move coin downward."""
        self.y += self.spd

    def off_screen(self) -> bool:
        return self.y - self.R > SCREEN_H

    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x - self.R, self.y - self.R,
                           self.R * 2, self.R * 2)


# ══════════════════════════════════════════════════════════════
#  HUD & OVERLAY HELPERS
# ══════════════════════════════════════════════════════════════

def draw_hud(surface, score: int, coin_count: int,
             speed_level: int, next_boost: int):
    """
    Draw the heads-up display:
      top-left  – current score
      top-right – coins collected
      below     – speed level and coins until next boost
    """
    score_surf = font.render(f"Score: {score}", True, WHITE)
    coin_surf  = font.render(f"Coins: {coin_count}", True, GOLD_COL)
    spd_surf   = small.render(
        f"Speed Lv {speed_level}  |  next boost in {next_boost} coin(s)",
        True, HUD_ORANGE
    )
    surface.blit(score_surf, (10, 8))
    surface.blit(coin_surf,  (SCREEN_W - coin_surf.get_width() - 10, 8))
    surface.blit(spd_surf,   (10, 35))


def draw_coin_legend(surface):
    """
    Draw a small legend at the bottom showing each coin tier and its value.
    Helps the player understand what each colour is worth.
    """
    x, y = 10, SCREEN_H - 22
    for tier in COIN_TYPES:
        pygame.draw.circle(surface, tier["colour"], (x + 5, y + 6), 6)
        lbl = small.render(f"+{tier['value']}", True, tier["colour"])
        surface.blit(lbl, (x + 14, y))
        x += 46   # move right for next tier


def draw_game_over(surface, score: int, coin_count: int):
    """
    Semi-transparent dark overlay with game-over statistics.
    Press R to restart or Q to quit.
    """
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    lines = [
        (big,   "GAME OVER",                   RED      ),
        (font,  f"Score : {score}",             WHITE    ),
        (font,  f"Coins : {coin_count}",        GOLD_COL ),
        (font,  "R – restart   Q – quit",       WHITE    ),
    ]
    y = 185
    for f_, text, col in lines:
        surf = f_.render(text, True, col)
        surface.blit(surf, (SCREEN_W // 2 - surf.get_width() // 2, y))
        y += surf.get_height() + 14


# ══════════════════════════════════════════════════════════════
#  MAIN GAME LOOP
# ══════════════════════════════════════════════════════════════

def main():
    road   = Road()
    player = PlayerCar()

    enemies: list[EnemyCar] = []
    coins:   list[Coin]     = []

    score        = 0
    coin_count   = 0          # total coins collected this session
    base_speed   = 4          # starting enemy / coin fall speed
    game_over    = False

    # ── spawn timers (counted in frames) ──
    enemy_timer    = 0
    enemy_interval = 80       # spawn an enemy every ~80 frames

    coin_timer     = 0
    coin_interval  = random.randint(100, 180)   # coins appear randomly

    # ── speed level tracking ──
    speed_level = 1           # displayed in HUD; starts at 1
    # coins_at_last_boost tracks when the last speed boost was granted
    coins_at_last_boost = 0

    while True:
        clock.tick(FPS)

        # ── EVENTS ────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and game_over:
                if event.key == pygame.K_r:
                    main()    # restart by re-calling main()
                    return
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

        # ── UPDATE (only while player is alive) ───────────────────────────
        if not game_over:
            keys = pygame.key.get_pressed()
            player.move(keys)
            road.update()

            # ── Compute current speed ──────────────────────────────────────
            # Base speed plus extra per coin boost threshold crossed
            coin_boosts    = coin_count // COINS_PER_BOOST   # how many boosts earned
            current_speed  = base_speed + coin_boosts * SPEED_BOOST
            speed_level    = coin_boosts + 1
            road.speed     = 5 + coin_boosts              # road also scrolls faster

            # Coins until the next speed boost (counts down to 0)
            next_boost     = COINS_PER_BOOST - (coin_count % COINS_PER_BOOST)

            # ── Spawn enemies ──────────────────────────────────────────────
            enemy_timer += 1
            if enemy_timer >= enemy_interval:
                enemies.append(EnemyCar(current_speed))
                enemy_timer    = 0
                enemy_interval = random.randint(55, 110)

            # ── Spawn coins (independent random timer) ─────────────────────
            coin_timer += 1
            if coin_timer >= coin_interval:
                coins.append(Coin(current_speed))
                coin_timer    = 0
                coin_interval = random.randint(90, 200)

            # ── Update enemies & check collisions ─────────────────────────
            for en in enemies[:]:
                en.update()
                if en.off_screen():
                    enemies.remove(en)
                    score += 1          # survived one enemy → +1 score
                elif en.rect().colliderect(player.rect()):
                    game_over = True    # collision → game over

            # ── Update coins & check collection ───────────────────────────
            for co in coins[:]:
                co.update()
                if co.off_screen():
                    coins.remove(co)    # coin missed – no penalty
                elif co.rect().colliderect(player.rect()):
                    coins.remove(co)
                    coin_count += co.value   # add the coin's weighted value
                    score      += co.value   # coins also add to score

        # ── DRAW ──────────────────────────────────────────────────────────
        road.draw(screen)               # scrolling road (clears screen too)

        for en in enemies:  en.draw(screen)
        for co in coins:    co.draw(screen)
        player.draw(screen)

        # HUD (always drawn, even on game over)
        draw_hud(screen, score, coin_count,
                 speed_level,
                 COINS_PER_BOOST - (coin_count % COINS_PER_BOOST))
        draw_coin_legend(screen)

        if game_over:
            draw_game_over(screen, score, coin_count)

        pygame.display.flip()


# ══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    main()

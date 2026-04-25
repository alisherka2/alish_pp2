import pygame
import random
import sys

CELL     = 20           # each grid square = 20 × 20 pixels
COLS     = 30           # number of columns in the play area
ROWS     = 28           # number of rows in the play area
SCREEN_W = COLS * CELL  # total window width  = 600 px
SCREEN_H = ROWS * CELL + 50   # total window height = 610 px (+50 for HUD)
HUD_H    = 50           # pixel height of the top status bar
FPS      = 10           # snake advances this many cells per second

UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)

BLACK      = (0,   0,   0  )
WHITE      = (255, 255, 255)
BG         = (30,  30,  30 )    # dark background for the grid
GRID_LINE  = (45,  45,  45 )    # subtle grid lines
SNAKE_HEAD = (0,   210, 80 )    # bright green for the head segment
SNAKE_BODY = (0,   160, 60 )    # darker green for body segments
SNAKE_EYE  = (255, 255, 255)
RED        = (220, 50,  50 )
YELLOW     = (255, 220, 0  )
ORANGE     = (255, 140, 0  )
PURPLE     = (180, 60,  200)
SILVER     = (192, 192, 192)

FOOD_TYPES = [
    {"label": "Apple",  "value": 1, "colour": RED,    "weight": 50, "lifetime": None},
    {"label": "Orange", "value": 2, "colour": ORANGE, "weight": 30, "lifetime": 50  },
    {"label": "Grape",  "value": 3, "colour": PURPLE, "weight": 15, "lifetime": 30  },
    {"label": "Star",   "value": 5, "colour": YELLOW, "weight": 5,  "lifetime": 20  },
]

MAX_FOOD_ON_SCREEN = 4

#  HELPER – weighted random selection

def weighted_choice(items: list) -> dict:
    total   = sum(i["weight"] for i in items)
    roll    = random.randint(1, total)
    running = 0
    for item in items:
        running += item["weight"]
        if roll <= running:
            return item
    return items[-1]   # safety fallback


# ══════════════════════════════════════════════════════════════
#  FOOD CLASS
# ══════════════════════════════════════════════════════════════

class Food:
    def __init__(self, occupied_cells: set):
        # Choose a random food type using weighted probability
        ftype          = weighted_choice(FOOD_TYPES)
        self.label     = ftype["label"]
        self.value     = ftype["value"]
        self.colour    = ftype["colour"]
        self.lifetime  = ftype["lifetime"]   # None means immortal
        self.age       = 0                   # frames this food has been alive

        # Find all free cells and pick one at random
        all_cells  = {(c, r) for c in range(COLS) for r in range(ROWS)}
        free_cells = list(all_cells - occupied_cells)
        self.pos   = random.choice(free_cells) if free_cells else (COLS // 2, ROWS // 2)

    def update(self) -> bool:
        """
        Increment the age counter.
        Returns True if the food has exceeded its lifetime and should be removed.
        Immortal food (lifetime=None) always returns False.
        """
        if self.lifetime is not None:
            self.age += 1
            return self.age >= self.lifetime
        return False   # immortal food never expires

    def time_fraction(self):
        """
        Return how much of the lifetime is still remaining as a float in [0, 1].
          1.0 = freshly spawned
          0.0 = about to disappear
        Returns None for immortal food.
        """
        if self.lifetime is None:
            return None
        return max(0.0, 1.0 - self.age / self.lifetime)

    def draw(self, surface):
        """
        Draw the food circle on `surface`.

        - Immortal food: solid filled circle, no fade.
        - Timed food:    alpha-blended circle that fades as time runs out,
                         plus a white ring to signal urgency.
        - All food:      score value printed in the centre.
        """
        col, row = self.pos

        # Convert grid position to pixel centre
        px = col * CELL + CELL // 2
        py = row * CELL + CELL // 2 + HUD_H

        fraction = self.time_fraction()

        if fraction is not None:
            # ── TIMED FOOD
            # Alpha goes from 255 (full opacity) down to 80 (nearly invisible)
            alpha = int(80 + 175 * fraction)

            # We need a per-pixel-alpha surface for transparency
            surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
            r, g, b = self.colour
            pygame.draw.circle(surf, (r, g, b, alpha),
                                (CELL // 2, CELL // 2), CELL // 2 - 2)
            surface.blit(surf, (col * CELL, row * CELL + HUD_H))

            # White urgency ring around timed food
            # (drawn directly on main surface; alpha approximated by colour)
            fade_white = (
                int(255 * fraction),
                int(255 * fraction),
                int(255 * fraction),
            )
            pygame.draw.circle(surface, fade_white, (px, py), CELL // 2 - 1, 2)

        else:
            # ── IMMORTAL FOOD: simple solid circle ───────────────────────
            pygame.draw.circle(surface, self.colour, (px, py), CELL // 2 - 2)

        # Score label centred on the food circle
        font_s = pygame.font.SysFont("arial", 11, bold=True)
        txt_col = BLACK if self.colour == YELLOW else WHITE
        txt = font_s.render(str(self.value), True, txt_col)
        surface.blit(txt, txt.get_rect(center=(px, py)))

#  SNAKE CLASS

class Snake:
    def __init__(self):
        # Start at the centre, 3 segments long, heading RIGHT
        mid_col, mid_row = COLS // 2, ROWS // 2
        self.body      = [(mid_col - i, mid_row) for i in range(3)]
        self.direction = RIGHT
        self.grew      = False   # set to True after eating food

    def change_direction(self, new_dir: tuple):
        opposite = (-self.direction[0], -self.direction[1])
        if new_dir != opposite:
            self.direction = new_dir

    def move(self):
        head     = self.body[0]
        new_head = (head[0] + self.direction[0],
                    head[1] + self.direction[1])
        self.body.insert(0, new_head)

        if not self.grew:
            self.body.pop()
        else:
            self.grew = False

    def head(self) -> tuple:
        """Return the (col, row) of the head segment."""
        return self.body[0]

    def is_dead(self) -> bool:
        hx, hy = self.head()

        # Check wall collision
        if not (0 <= hx < COLS and 0 <= hy < ROWS):
            return True

        # Check self-collision (body[1:] skips the head itself)
        if self.head() in self.body[1:]:
            return True

        return False

    def occupied_cells(self) -> set:
        """Return a set of all (col, row) cells occupied by the snake."""
        return set(self.body)

    def draw(self, surface):
        for i, (col, row) in enumerate(self.body):
            px = col * CELL
            py = row * CELL + HUD_H
            colour = SNAKE_HEAD if i == 0 else SNAKE_BODY
            pygame.draw.rect(surface, colour,
                             (px + 1, py + 1, CELL - 2, CELL - 2),
                             border_radius=4)

        # ── Eyes ──────────────────────────────────────────────────────────
        hx, hy = self.body[0]
        cx = hx * CELL + CELL // 2
        cy = hy * CELL + CELL // 2 + HUD_H
        dx, dy = self.direction

        # Perpendicular vector for placing eyes on either side of the head
        perp = (-dy, dx)
        for side in (+1, -1):
            ex = cx + dx * 4 + perp[0] * side * 4
            ey = cy + dy * 4 + perp[1] * side * 4
            pygame.draw.circle(surface, SNAKE_EYE, (ex, ey), 3)   # white of eye
            pygame.draw.circle(surface, BLACK, (ex + dx, ey + dy), 1)  # pupil


# ══════════════════════════════════════════════════════════════
#  MAIN GAME CONTROLLER
# ══════════════════════════════════════════════════════════════

class SnakeGame:
    """
    Top-level controller that owns the game loop, all game objects,
    and the pygame window.
    """

    FOOD_SPAWN_INTERVAL = 25   # try to spawn a new food every 25 frames

    def __init__(self):
        pygame.init()
        self.screen     = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Snake – Practice 11")
        self.clock      = pygame.time.Clock()
        self.font       = pygame.font.SysFont("arial", 22, bold=True)
        self.big_font   = pygame.font.SysFont("arial", 48, bold=True)
        self.small_font = pygame.font.SysFont("arial", 13)
        self.reset()   # initialise / reset all game state

    def reset(self):
        """
        Reset all mutable game state for a fresh game.
        Called once at startup and again when the player presses R.
        """
        self.snake     = Snake()
        self.foods     = []      # list of active Food objects
        self.score     = 0
        self.frame     = 0       # frame counter used for spawn timing
        self.game_over = False
        self.running   = True

        # Spawn the first food immediately so the snake has something to eat
        self._try_spawn_food()

    # ══════════════════════════════════════════════════════════
    #  MAIN LOOP
    # ══════════════════════════════════════════════════════════

    def run(self):
        """Run the game loop until the player quits."""
        while self.running:
            self.clock.tick(FPS)      # enforce constant FPS (= snake speed)
            self._handle_events()
            if not self.game_over:
                self._update()
            self._draw()
        pygame.quit()
        sys.exit()

    # ══════════════════════════════════════════════════════════
    #  EVENT HANDLING
    # ══════════════════════════════════════════════════════════

    def _handle_events(self):
        """Process all queued pygame events (keyboard & window close)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                # Direction controls (arrow keys and WASD both work)
                if   event.key in (pygame.K_UP,    pygame.K_w):
                    self.snake.change_direction(UP)
                elif event.key in (pygame.K_DOWN,  pygame.K_s):
                    self.snake.change_direction(DOWN)
                elif event.key in (pygame.K_LEFT,  pygame.K_a):
                    self.snake.change_direction(LEFT)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.snake.change_direction(RIGHT)

                # Restart only works after game over
                elif event.key == pygame.K_r and self.game_over:
                    self.reset()

                # Quit any time
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

    # ══════════════════════════════════════════════════════════
    #  GAME UPDATE (one frame)
    # ══════════════════════════════════════════════════════════

    def _update(self):
        """
        Advance all game logic by one frame:
          1. Move the snake.
          2. Check for death.
          3. Check food collection.
          4. Tick food timers and remove expired food.
          5. Possibly spawn new food.
        """
        self.frame += 1

        # ── 1. Move snake ─────────────────────────────────────────────────
        self.snake.move()

        # ── 2. Death check ────────────────────────────────────────────────
        if self.snake.is_dead():
            self.game_over = True
            return   # stop further processing this frame

        # ── 3. Food collection ────────────────────────────────────────────
        head = self.snake.head()
        for food in self.foods[:]:      # iterate over a copy so we can remove
            if food.pos == head:
                self.score      += food.value   # add the food's weighted score
                self.snake.grew  = True         # signal snake to grow next move
                self.foods.remove(food)

        # ── 4. Food timers – remove expired timed food ────────────────────
        for food in self.foods[:]:
            if food.update():           # update() returns True when expired
                self.foods.remove(food)

        # ── 5. Spawn new food periodically ───────────────────────────────
        if self.frame % self.FOOD_SPAWN_INTERVAL == 0:
            self._try_spawn_food()

    def _try_spawn_food(self):
        """
        Spawn a new food item if the on-screen count is below MAX_FOOD_ON_SCREEN.
        Passes the current occupied cells to Food() so it won't overlap.
        """
        if len(self.foods) < MAX_FOOD_ON_SCREEN:
            # Combine snake cells and existing food positions
            occupied = self.snake.occupied_cells() | {f.pos for f in self.foods}
            self.foods.append(Food(occupied))

    # ══════════════════════════════════════════════════════════
    #  DRAWING
    # ══════════════════════════════════════════════════════════

    def _draw(self):
        """Render the entire frame: background → grid → food → snake → HUD."""
        self.screen.fill(BG)

        # Draw subtle grid lines so the player can count cells
        for c in range(COLS):
            for r in range(ROWS):
                pygame.draw.rect(self.screen, GRID_LINE,
                                 (c * CELL, r * CELL + HUD_H, CELL, CELL), 1)

        # Food items (drawn before snake so snake appears on top)
        for food in self.foods:
            food.draw(self.screen)

        # Snake body and head
        self.snake.draw(self.screen)

        # HUD strip at the top
        self._draw_hud()

        # Food legend inside the HUD (right side)
        self._draw_legend()

        # Game-over overlay (rendered last so it covers everything)
        if self.game_over:
            self._draw_game_over()

        pygame.display.flip()   # push rendered frame to the display

    def _draw_hud(self):
        # Dark background panel behind the HUD
        pygame.draw.rect(self.screen, (20, 20, 20), (0, 0, SCREEN_W, HUD_H))
        # Yellow separator line between HUD and play area
        pygame.draw.line(self.screen, YELLOW, (0, HUD_H), (SCREEN_W, HUD_H), 2)

        score_txt  = self.font.render(f"Score: {self.score}", True, YELLOW)
        length_txt = self.font.render(f"Length: {len(self.snake.body)}", True, WHITE)
        ctrl_txt   = self.small_font.render(
            "Arrows / WASD to move  |  R = restart  |  ESC = quit",
            True, SILVER
        )

        self.screen.blit(score_txt,  (10, 12))
        self.screen.blit(length_txt, (200, 12))
        self.screen.blit(ctrl_txt,   (10, HUD_H - 16))

    def _draw_legend(self):
        """
        Food type legend on the right side of the HUD.
        Shows each food's colour, name, score value, and lifetime in frames.
        """
        x = SCREEN_W - 195
        # Background for the legend area
        pygame.draw.rect(self.screen, (20, 20, 20), (x - 5, 0, 200, HUD_H - 18))

        for i, ft in enumerate(FOOD_TYPES):
            # 2-column layout: items 0,2 → left column; 1,3 → right column
            lx = x + (i % 2) * 95
            ly = 6 + (i // 2) * 18

            # Colour dot
            pygame.draw.circle(self.screen, ft["colour"], (lx + 7, ly + 7), 7)

            # Label text: name, score, and lifetime (if applicable)
            label = f"{ft['label']} +{ft['value']}"
            if ft["lifetime"]:
                label += f" {ft['lifetime']}f"   # 'f' = frames

            txt = self.small_font.render(label, True, ft["colour"])
            self.screen.blit(txt, (lx + 18, ly))

    def _draw_game_over(self):
        """
        Semi-transparent overlay displayed when the snake dies.
        Shows final score and length, and prompts for R (restart) or ESC (quit).
        """
        # Dark semi-transparent panel
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))   # RGBA: 160 = ~63 % opaque
        self.screen.blit(overlay, (0, 0))

        go  = self.big_font.render("GAME OVER", True, RED)
        sc  = self.font.render(
            f"Score: {self.score}  |  Length: {len(self.snake.body)}", True, YELLOW
        )
        rst = self.font.render(
            "Press  R  to Restart   |   ESC to Quit", True, WHITE
        )

        cx = SCREEN_W // 2
        cy = SCREEN_H // 2
        self.screen.blit(go,  go.get_rect(center=(cx, cy - 50)))
        self.screen.blit(sc,  sc.get_rect(center=(cx, cy + 10)))
        self.screen.blit(rst, rst.get_rect(center=(cx, cy + 50)))


# ══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    game = SnakeGame()
    game.run()

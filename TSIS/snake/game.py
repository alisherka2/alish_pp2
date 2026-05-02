# game.py — Snake game engine (TSIS4: all features)

import pygame
import random
import json
import os

from config import *
import db as db_module

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_settings() -> dict:
    defaults = {"snake_color": list(SNAKE_HEAD), "grid_overlay": True, "sound": False}
    try:
        with open(SETTINGS_PATH) as f:
            data = json.load(f)
        defaults.update(data)
    except Exception:
        pass
    return defaults


def save_settings(settings: dict):
    try:
        with open(SETTINGS_PATH, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"[Settings] save error: {e}")


def weighted_choice(items):
    total   = sum(i["weight"] for i in items)
    roll    = random.randint(1, total)
    running = 0
    for item in items:
        running += item["weight"]
        if roll <= running:
            return item
    return items[-1]


def _free_cells(snake_cells: set, food_positions: set,
                obstacle_cells: set) -> list:
    all_cells = {(c, r) for c in range(COLS) for r in range(ROWS)}
    return list(all_cells - snake_cells - food_positions - obstacle_cells)


# ── Food ─────────────────────────────────────────────────────────────────────

class Food:
    def __init__(self, occupied: set, poison: bool = False):
        self.poison   = poison
        self.age      = 0
        if poison:
            self.label    = "Poison"
            self.value    = 0
            self.colour   = DARK_RED
            self.lifetime = 60
        else:
            ftype         = weighted_choice(FOOD_TYPES)
            self.label    = ftype["label"]
            self.value    = ftype["value"]
            self.colour   = ftype["colour"]
            self.lifetime = ftype["lifetime"]

        free = _free_cells(occupied, set(), set())
        self.pos = random.choice(free) if free else (COLS // 2, ROWS // 2)

    def update(self) -> bool:
        if self.lifetime is not None:
            self.age += 1
            return self.age >= self.lifetime
        return False

    def time_fraction(self):
        if self.lifetime is None:
            return None
        return max(0.0, 1.0 - self.age / self.lifetime)

    def draw(self, surface):
        col, row = self.pos
        px = col * CELL + CELL // 2
        py = row * CELL + CELL // 2 + HUD_H
        fraction = self.time_fraction()

        if fraction is not None:
            alpha = int(80 + 175 * fraction)
            surf  = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
            r, g, b = self.colour
            pygame.draw.circle(surf, (r, g, b, alpha),
                                (CELL // 2, CELL // 2), CELL // 2 - 2)
            surface.blit(surf, (col * CELL, row * CELL + HUD_H))
            fade = (int(255 * fraction),) * 3
            pygame.draw.circle(surface, fade, (px, py), CELL // 2 - 1, 2)
        else:
            pygame.draw.circle(surface, self.colour, (px, py), CELL // 2 - 2)

        # Skull for poison food
        if self.poison:
            font_s = pygame.font.SysFont("arial", 14, bold=True)
            txt = font_s.render("☠", True, WHITE)
            surface.blit(txt, txt.get_rect(center=(px, py)))
        else:
            font_s = pygame.font.SysFont("arial", 11, bold=True)
            txt_col = BLACK if self.colour == YELLOW else WHITE
            txt = font_s.render(str(self.value), True, txt_col)
            surface.blit(txt, txt.get_rect(center=(px, py)))


# ── Power-up ──────────────────────────────────────────────────────────────────

class PowerUp:
    def __init__(self, occupied: set):
        ptype        = random.choice(POWERUP_TYPES)
        self.label   = ptype["label"]
        self.colour  = ptype["colour"]
        self.kind    = ptype["kind"]
        self.spawned_at = pygame.time.get_ticks()  # ms

        free = _free_cells(occupied, set(), set())
        self.pos = random.choice(free) if free else (1, 1)

    def expired_on_field(self) -> bool:
        return pygame.time.get_ticks() - self.spawned_at > POWERUP_FIELD_TIMEOUT_MS

    def draw(self, surface):
        col, row = self.pos
        px = col * CELL + CELL // 2
        py = row * CELL + CELL // 2 + HUD_H
        # Pulsing ring
        elapsed  = pygame.time.get_ticks() - self.spawned_at
        fraction = max(0.0, 1.0 - elapsed / POWERUP_FIELD_TIMEOUT_MS)
        alpha    = int(120 + 135 * fraction)

        surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        r, g, b = self.colour
        pygame.draw.circle(surf, (r, g, b, alpha),
                            (CELL // 2, CELL // 2), CELL // 2 - 1)
        surface.blit(surf, (col * CELL, row * CELL + HUD_H))
        pygame.draw.circle(surface, WHITE, (px, py), CELL // 2 - 1, 2)

        font_s = pygame.font.SysFont("arial", 9, bold=True)
        label_map = {"speed": "⚡", "slow": "🐢", "shield": "🛡"}
        lbl = label_map.get(self.kind, "?")
        txt = font_s.render(lbl, True, BLACK)
        surface.blit(txt, txt.get_rect(center=(px, py)))


# ── Snake ─────────────────────────────────────────────────────────────────────

class Snake:
    def __init__(self, color):
        mid_col, mid_row = COLS // 2, ROWS // 2
        self.body      = [(mid_col - i, mid_row) for i in range(3)]
        self.direction = RIGHT
        self.grew      = False
        self.color     = tuple(color)

    def change_direction(self, new_dir):
        opposite = (-self.direction[0], -self.direction[1])
        if new_dir != opposite:
            self.direction = new_dir

    def move(self, shield_active: bool = False) -> bool:
        """
        Move the snake one step. Returns True if a wall was crossed
        (so the caller can consume the shield).
        """
        head = self.body[0]
        nx = head[0] + self.direction[0]
        ny = head[1] + self.direction[1]

        wall_crossed = not (0 <= nx < COLS and 0 <= ny < ROWS)

        # With shield: wrap through the opposite wall
        if shield_active and wall_crossed:
            nx = nx % COLS
            ny = ny % ROWS

        new_head = (nx, ny)
        self.body.insert(0, new_head)
        if not self.grew:
            self.body.pop()
        else:
            self.grew = False

        return wall_crossed and shield_active

    def head(self):
        return self.body[0]

    def is_dead(self, obstacles: set, shield_active: bool) -> bool:
        hx, hy = self.head()
        # Wall collision: with shield active the snake wraps, so never deadly
        if not (0 <= hx < COLS and 0 <= hy < ROWS):
            return not shield_active
        # Self-collision and obstacle collision still kill even with shield
        if self.head() in self.body[1:]:
            return True
        if self.head() in obstacles:
            return True
        return False

    def shorten(self, n: int):
        """Remove up to n tail segments."""
        for _ in range(n):
            if len(self.body) > 1:
                self.body.pop()

    def occupied_cells(self) -> set:
        return set(self.body)

    def draw(self, surface, head_color=None, body_color=None):
        hc = tuple(head_color) if head_color else self.color
        # Darken body color slightly
        bc = tuple(max(0, c - 50) for c in hc) if body_color is None else body_color

        for i, (col, row) in enumerate(self.body):
            px = col * CELL
            py = row * CELL + HUD_H
            colour = hc if i == 0 else bc
            pygame.draw.rect(surface, colour,
                             (px + 1, py + 1, CELL - 2, CELL - 2),
                             border_radius=4)

        hx, hy = self.body[0]
        cx = hx * CELL + CELL // 2
        cy = hy * CELL + CELL // 2 + HUD_H
        dx, dy = self.direction
        perp = (-dy, dx)
        for side in (+1, -1):
            ex = cx + dx * 4 + perp[0] * side * 4
            ey = cy + dy * 4 + perp[1] * side * 4
            pygame.draw.circle(surface, SNAKE_EYE, (ex, ey), 3)
            pygame.draw.circle(surface, BLACK, (ex + dx, ey + dy), 1)


# ── Obstacle ──────────────────────────────────────────────────────────────────

def generate_obstacles(snake_cells: set, existing: set, count: int) -> set:
    """Place `count` new obstacles that don't overlap snake or existing obstacles."""
    free = list(
        {(c, r) for c in range(COLS) for r in range(ROWS)}
        - snake_cells - existing
    )
    # Keep snake head + 3-cell buffer free
    head = next(iter(snake_cells))  # approximate
    free = [p for p in free
            if abs(p[0] - head[0]) + abs(p[1] - head[1]) > 3]
    random.shuffle(free)
    new_obs = set()
    for cell in free[:count]:
        new_obs.add(cell)
    return new_obs


# ── SnakeGame ─────────────────────────────────────────────────────────────────

class SnakeGame:
    FOOD_SPAWN_INTERVAL = FOOD_SPAWN_INTERVAL

    def __init__(self, username: str, player_id):
        self.username  = username
        self.player_id = player_id
        self.settings  = load_settings()

        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Snake — TSIS4")
        self.clock     = pygame.time.Clock()
        self.font      = pygame.font.SysFont("arial", 20, bold=True)
        self.small_font= pygame.font.SysFont("arial", 13)
        self.big_font  = pygame.font.SysFont("arial", 48, bold=True)

        self.personal_best = db_module.get_personal_best(player_id)
        self.result        = None   # filled in after game over

        self.reset()

    # ── State reset ──────────────────────────────────────────────────────────

    def reset(self):
        color        = self.settings.get("snake_color", list(SNAKE_HEAD))
        self.snake   = Snake(color)
        self.foods   = []
        self.poison_food = None
        self.powerup = None          # at most one on screen
        self.score   = 0
        self.frame   = 0
        self.level   = 1
        self.food_eaten_this_level = 0
        self.game_over = False
        self.running   = True
        self.obstacles : set = set()

        # Active effect tracking
        self.current_fps       = BASE_FPS
        self.effect_kind       = None    # "speed" | "slow" | "shield"
        self.effect_end_ms     = 0
        self.shield_active     = False
        self.shield_used       = False   # shield is consumed on first collision

        self._try_spawn_food()

    # ── Public run loop ──────────────────────────────────────────────────────

    def run(self) -> str:
        """
        Run the game. Returns "menu" or "quit".
        """
        while self.running:
            self.clock.tick(self.current_fps)
            result = self._handle_events()
            if result:
                return result
            if not self.game_over:
                self._update()
            self._draw()
        return "quit"

    # ── Events ───────────────────────────────────────────────────────────────

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return "quit"
            if event.type == pygame.KEYDOWN:
                if   event.key in (pygame.K_UP,    pygame.K_w):
                    self.snake.change_direction(UP)
                elif event.key in (pygame.K_DOWN,  pygame.K_s):
                    self.snake.change_direction(DOWN)
                elif event.key in (pygame.K_LEFT,  pygame.K_a):
                    self.snake.change_direction(LEFT)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.snake.change_direction(RIGHT)
                elif event.key == pygame.K_r and self.game_over:
                    self.reset()
                elif event.key == pygame.K_m and self.game_over:
                    return "menu"
                elif event.key == pygame.K_ESCAPE:
                    return "menu"
        return None

    # ── Update ───────────────────────────────────────────────────────────────

    def _update(self):
        self.frame += 1
        now = pygame.time.get_ticks()

        # ── Effect expiry ─────────────────────────────────────────────────────
        if self.effect_kind and now >= self.effect_end_ms:
            self._clear_effect()

        # ── Move (wall-wrap when shield active) ──────────────────────────────
        wall_crossed = self.snake.move(shield_active=self.shield_active)

        # Shield is consumed the moment it wraps through a wall (one use only)
        if wall_crossed and self.shield_active:
            self.shield_active = False
            self.effect_kind   = None

        # ── Collision check ───────────────────────────────────────────────────
        if self.snake.is_dead(self.obstacles, self.shield_active):
            self._trigger_game_over()
            return

        # ── Normal food collection ─────────────────────────────────────────────
        head = self.snake.head()
        for food in self.foods[:]:
            if food.pos == head:
                self.score += food.value
                self.snake.grew = True
                self.foods.remove(food)
                self.food_eaten_this_level += 1
                self._check_level_up()

        # ── Poison food ───────────────────────────────────────────────────────
        if self.poison_food and self.poison_food.pos == head:
            self.snake.shorten(2)
            self.poison_food = None
            if len(self.snake.body) <= 1:
                self._trigger_game_over()
                return

        # ── Power-up collection ───────────────────────────────────────────────
        if self.powerup and self.powerup.pos == head:
            self._apply_powerup(self.powerup.kind)
            self.powerup = None

        # ── Food timers ───────────────────────────────────────────────────────
        for food in self.foods[:]:
            if food.update():
                self.foods.remove(food)
        if self.poison_food and self.poison_food.update():
            self.poison_food = None

        # ── Spawn food ────────────────────────────────────────────────────────
        if self.frame % self.FOOD_SPAWN_INTERVAL == 0:
            self._try_spawn_food()

        # ── Spawn poison food (every ~120 frames) ────────────────────────────
        if self.poison_food is None and self.frame % 120 == 0:
            occupied = self._all_occupied()
            free = _free_cells(occupied, set(), self.obstacles)
            if free:
                self.poison_food = Food(occupied, poison=True)

        # ── Spawn / expire power-up ───────────────────────────────────────────
        if self.powerup and self.powerup.expired_on_field():
            self.powerup = None
        if self.powerup is None and self.frame % POWERUP_SPAWN_INTERVAL == 0:
            occupied = self._all_occupied()
            self.powerup = PowerUp(occupied)

    def _all_occupied(self) -> set:
        occupied  = self.snake.occupied_cells()
        occupied |= {f.pos for f in self.foods}
        occupied |= self.obstacles
        if self.poison_food:
            occupied.add(self.poison_food.pos)
        if self.powerup:
            occupied.add(self.powerup.pos)
        return occupied

    def _try_spawn_food(self):
        if len(self.foods) < MAX_FOOD_ON_SCREEN:
            occupied = self._all_occupied()
            self.foods.append(Food(occupied))

    def _check_level_up(self):
        if self.food_eaten_this_level >= LEVEL_FOOD_THRESHOLD:
            self.level += 1
            self.food_eaten_this_level = 0
            # Increase base speed slightly
            self.current_fps = BASE_FPS + (self.level - 1) * 2
            # Add obstacles from level 3 onward
            if self.level >= 3:
                new_obs = generate_obstacles(
                    self.snake.occupied_cells(),
                    self.obstacles,
                    OBSTACLE_COUNT_PER_LEVEL
                )
                self.obstacles |= new_obs

    def _apply_powerup(self, kind: str):
        now = pygame.time.get_ticks()
        self.effect_kind   = kind
        self.effect_end_ms = now + POWERUP_EFFECT_MS
        if kind == "speed":
            self.current_fps = self.current_fps + 8
        elif kind == "slow":
            self.current_fps = max(3, self.current_fps - 5)
        elif kind == "shield":
            self.shield_active = True

    def _clear_effect(self):
        kind = self.effect_kind
        self.effect_kind = None
        # Restore FPS to level-appropriate value
        base = BASE_FPS + (self.level - 1) * 2
        if kind in ("speed", "slow"):
            self.current_fps = base
        elif kind == "shield":
            self.shield_active = False

    def _trigger_game_over(self):
        self.game_over = True
        db_module.save_session(self.player_id, self.score, self.level)
        if self.score > self.personal_best:
            self.personal_best = self.score

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw(self):
        self.screen.fill(BG)

        if self.settings.get("grid_overlay", True):
            for c in range(COLS):
                for r in range(ROWS):
                    pygame.draw.rect(self.screen, GRID_LINE,
                                     (c * CELL, r * CELL + HUD_H, CELL, CELL), 1)

        # Obstacles
        for (c, r) in self.obstacles:
            pygame.draw.rect(self.screen, OBSTACLE,
                             (c * CELL + 1, r * CELL + HUD_H + 1, CELL - 2, CELL - 2))

        for food in self.foods:
            food.draw(self.screen)
        if self.poison_food:
            self.poison_food.draw(self.screen)
        if self.powerup:
            self.powerup.draw(self.screen)

        # Shield glow
        if self.shield_active:
            hx, hy = self.snake.head()
            px = hx * CELL + CELL // 2
            py = hy * CELL + CELL // 2 + HUD_H
            pygame.draw.circle(self.screen, GOLD, (px, py), CELL, 3)

        self.snake.draw(self.screen)
        self._draw_hud()
        self._draw_legend()

        if self.game_over:
            self._draw_game_over()

        pygame.display.flip()

    def _draw_hud(self):
        pygame.draw.rect(self.screen, (20, 20, 20), (0, 0, SCREEN_W, HUD_H))
        pygame.draw.line(self.screen, YELLOW, (0, HUD_H), (SCREEN_W, HUD_H), 2)

        now = pygame.time.get_ticks()
        effect_str = ""
        if self.effect_kind and now < self.effect_end_ms:
            secs = (self.effect_end_ms - now) // 1000
            label_map = {"speed": "⚡Speed", "slow": "🐢Slow", "shield": "🛡Shield"}
            effect_str = f"  [{label_map.get(self.effect_kind,'')} {secs}s]"

        score_txt  = self.font.render(f"Score: {self.score}", True, YELLOW)
        level_txt  = self.font.render(f"Lvl: {self.level}", True, CYAN)
        best_txt   = self.font.render(f"Best: {self.personal_best}", True, SILVER)
        ctrl_txt   = self.small_font.render(
            f"Arrows/WASD  R=restart  M=menu  ESC=menu{effect_str}", True, SILVER)

        self.screen.blit(score_txt, (10,  8))
        self.screen.blit(level_txt, (160, 8))
        self.screen.blit(best_txt,  (240, 8))
        self.screen.blit(ctrl_txt,  (10, HUD_H - 16))

    def _draw_legend(self):
        x = SCREEN_W - 195
        pygame.draw.rect(self.screen, (20, 20, 20), (x - 5, 0, 200, HUD_H - 18))
        for i, ft in enumerate(FOOD_TYPES):
            lx = x + (i % 2) * 95
            ly = 6  + (i // 2) * 18
            pygame.draw.circle(self.screen, ft["colour"], (lx + 7, ly + 7), 7)
            label = f"{ft['label']} +{ft['value']}"
            if ft["lifetime"]:
                label += f" {ft['lifetime']}f"
            txt = self.small_font.render(label, True, ft["colour"])
            self.screen.blit(txt, (lx + 18, ly))

    def _draw_game_over(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        cx, cy = SCREEN_W // 2, SCREEN_H // 2
        texts = [
            (self.big_font, "GAME OVER",                          RED,    -70),
            (self.font,     f"Score: {self.score}  |  Level: {self.level}", YELLOW, -10),
            (self.font,     f"Personal Best: {self.personal_best}",SILVER,  30),
            (self.font,     "R = Restart   M = Menu",              WHITE,   70),
        ]
        for font, text, colour, dy in texts:
            surf = font.render(text, True, colour)
            self.screen.blit(surf, surf.get_rect(center=(cx, cy + dy)))

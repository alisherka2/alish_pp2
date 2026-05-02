"""
ui.py  –  TSIS 3
All non-gameplay screen rendering:
  draw_main_menu, draw_settings, draw_leaderboard, draw_game_over, draw_hud
Returns the name of the next state so main.py stays state-machine clean.
"""
import pygame
from persistence import CAR_COLORS, DIFFICULTY_SETTINGS

# ── shared colours ──────────────────────────────────────────────
WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0  )
GRAY   = (130, 130, 130)
DKGRAY = (28,  28,  40 )
RED    = (210, 30,  30 )
GOLD   = (255, 215,  0 )
GREEN  = (80,  220,  80)
ORANGE = (255, 160,   0)
CYAN   = (0,   200, 220)
TEAL   = (0,   160, 140)

SCREEN_W = 400
SCREEN_H = 600


# ════════════════════════════════════════════════════════════════
#  GENERIC BUTTON
# ════════════════════════════════════════════════════════════════

class Button:
    def __init__(self, text, rect, color=TEAL, text_color=WHITE, font=None):
        self.text       = text
        self.rect       = pygame.Rect(rect)
        self.color      = color
        self.text_color = text_color
        self.font       = font

    def draw(self, surface):
        f = self.font or pygame.font.SysFont("Arial", 20, bold=True)
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        col   = tuple(min(255, c + 30) for c in self.color) if hover else self.color
        pygame.draw.rect(surface, col,   self.rect, border_radius=8)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=8)
        lbl = f.render(self.text, True, self.text_color)
        surface.blit(lbl, lbl.get_rect(center=self.rect.center))

    def clicked(self, event) -> bool:
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


# ════════════════════════════════════════════════════════════════
#  INPUT BOX  (username entry)
# ════════════════════════════════════════════════════════════════

class InputBox:
    def __init__(self, rect, placeholder=""):
        self.rect        = pygame.Rect(rect)
        self.placeholder = placeholder
        self.text        = ""
        self.active      = False
        self.font        = pygame.font.SysFont("Consolas", 20)

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key not in (pygame.K_RETURN, pygame.K_ESCAPE):
                if len(self.text) < 16 and event.unicode.isprintable():
                    self.text += event.unicode

    def draw(self, surface):
        border = WHITE if self.active else GRAY
        pygame.draw.rect(surface, (40, 40, 55), self.rect, border_radius=6)
        pygame.draw.rect(surface, border, self.rect, 2, border_radius=6)
        display = self.text or self.placeholder
        color   = WHITE if self.text else GRAY
        lbl = self.font.render(display, True, color)
        surface.blit(lbl, (self.rect.x + 8, self.rect.y + 6))


# ════════════════════════════════════════════════════════════════
#  MAIN MENU
# ════════════════════════════════════════════════════════════════

def run_main_menu(screen, clock, settings):
    """Blocking. Returns 'play' | 'leaderboard' | 'settings' | 'quit'."""
    font_big  = pygame.font.SysFont("Arial", 44, bold=True)
    font_sub  = pygame.font.SysFont("Arial", 16)

    bw, bh = 220, 46
    cx = SCREEN_W // 2 - bw // 2
    btns = [
        Button("▶  Play",        (cx, 210, bw, bh), TEAL),
        Button("🏆  Leaderboard", (cx, 270, bw, bh), (70, 90, 160)),
        Button("⚙  Settings",    (cx, 330, bw, bh), (80, 80, 80)),
        Button("✕  Quit",        (cx, 390, bw, bh), (140, 30, 30)),
    ]
    actions = ["play", "leaderboard", "settings", "quit"]

    username_box = InputBox((cx, 148, bw, 36), placeholder="Enter your name…")
    if settings.get("username"):
        username_box.text = settings["username"]

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            username_box.handle(event)
            for i, btn in enumerate(btns):
                if btn.clicked(event):
                    settings["username"] = username_box.text.strip() or "Player"
                    return actions[i]

        # background
        screen.fill(DKGRAY)
        _draw_road_bg(screen)

        # title
        t = font_big.render("RACER", True, GOLD)
        screen.blit(t, t.get_rect(center=(SCREEN_W // 2, 80)))
        sub = font_sub.render("TSIS 3 Edition", True, GRAY)
        screen.blit(sub, sub.get_rect(center=(SCREEN_W // 2, 120)))

        # username label
        lbl = pygame.font.SysFont("Arial", 14).render("Your name:", True, GRAY)
        screen.blit(lbl, (cx, 132))
        username_box.draw(screen)

        for btn in btns:
            btn.draw(screen)

        pygame.display.flip()


# ════════════════════════════════════════════════════════════════
#  SETTINGS SCREEN
# ════════════════════════════════════════════════════════════════

def run_settings(screen, clock, settings):
    """Blocking. Returns updated settings dict."""
    font  = pygame.font.SysFont("Arial", 20, bold=True)
    small = pygame.font.SysFont("Arial", 15)
    title = pygame.font.SysFont("Arial", 36, bold=True)

    back_btn = Button("← Back", (20, 540, 120, 38), (80, 80, 80))

    car_colors  = list(CAR_COLORS.keys())
    difficulties = list(DIFFICULTY_SETTINGS.keys())

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return settings
            if back_btn.clicked(event):
                return settings

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # Sound toggle
                if pygame.Rect(270, 130, 100, 36).collidepoint(mx, my):
                    settings["sound"] = not settings["sound"]

                # Car colour cycle
                if pygame.Rect(270, 200, 100, 36).collidepoint(mx, my):
                    idx = car_colors.index(settings["car_color"])
                    settings["car_color"] = car_colors[(idx + 1) % len(car_colors)]

                # Difficulty cycle
                if pygame.Rect(270, 270, 100, 36).collidepoint(mx, my):
                    idx = difficulties.index(settings["difficulty"])
                    settings["difficulty"] = difficulties[(idx + 1) % len(difficulties)]

        screen.fill(DKGRAY)
        t = title.render("Settings", True, WHITE)
        screen.blit(t, t.get_rect(center=(SCREEN_W // 2, 60)))

        rows = [
            ("Sound",       str(settings["sound"]),      130),
            ("Car Color",   settings["car_color"],        200),
            ("Difficulty",  settings["difficulty"],       270),
        ]
        for label, value, y in rows:
            lbl = font.render(label + ":", True, GRAY)
            screen.blit(lbl, (40, y + 8))
            btn_rect = pygame.Rect(270, y, 100, 36)
            pygame.draw.rect(screen, TEAL, btn_rect, border_radius=6)
            pygame.draw.rect(screen, WHITE, btn_rect, 2, border_radius=6)
            val = small.render(value.capitalize(), True, WHITE)
            screen.blit(val, val.get_rect(center=btn_rect.center))

        # car colour preview
        col = CAR_COLORS[settings["car_color"]]
        pygame.draw.rect(screen, col, (160, 196, 38, 44), border_radius=6)

        back_btn.draw(screen)
        pygame.display.flip()


# ════════════════════════════════════════════════════════════════
#  LEADERBOARD SCREEN
# ════════════════════════════════════════════════════════════════

def run_leaderboard(screen, clock, board):
    """Blocking. Returns when user clicks Back."""
    font_title = pygame.font.SysFont("Arial", 34, bold=True)
    font_hdr   = pygame.font.SysFont("Arial", 14, bold=True)
    font_row   = pygame.font.SysFont("Arial", 16)
    back_btn   = Button("← Back", (20, 540, 120, 38), (80, 80, 80))

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if back_btn.clicked(event):
                return

        screen.fill(DKGRAY)
        t = font_title.render("🏆 Leaderboard", True, GOLD)
        screen.blit(t, t.get_rect(center=(SCREEN_W // 2, 50)))

        # header
        cols = [(20,"#"),(50,"Name"),(160,"Score"),(250,"Dist"),(320,"Coins")]
        for x, h in cols:
            lbl = font_hdr.render(h, True, GRAY)
            screen.blit(lbl, (x, 90))
        pygame.draw.line(screen, GRAY, (20, 108), (380, 108), 1)

        for i, entry in enumerate(board[:10]):
            y   = 116 + i * 38
            col = GOLD if i == 0 else (GRAY if i == 1 else WHITE)
            data = [
                (20,  f"{i+1}."),
                (50,  entry.get("name","?")[:10]),
                (160, str(entry.get("score", 0))),
                (250, f"{entry.get('distance',0)}m"),
                (320, str(entry.get("coins", 0))),
            ]
            for x, text in data:
                lbl = font_row.render(text, True, col)
                screen.blit(lbl, (x, y))

        if not board:
            empty = font_row.render("No scores yet – play a game!", True, GRAY)
            screen.blit(empty, empty.get_rect(center=(SCREEN_W // 2, 250)))

        back_btn.draw(screen)
        pygame.display.flip()


# ════════════════════════════════════════════════════════════════
#  GAME OVER SCREEN
# ════════════════════════════════════════════════════════════════

def run_game_over(screen, clock, score, distance, coins):
    """Blocking. Returns 'retry' | 'menu'."""
    font_big  = pygame.font.SysFont("Arial", 46, bold=True)
    font      = pygame.font.SysFont("Arial", 22, bold=True)

    bw, bh = 160, 46
    retry_btn = Button("↺  Retry",     (40,  400, bw, bh), TEAL)
    menu_btn  = Button("⌂  Main Menu", (200, 400, bw, bh), (80,80,80))

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if retry_btn.clicked(event):
                return "retry"
            if menu_btn.clicked(event):
                return "menu"

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        t = font_big.render("GAME OVER", True, RED)
        screen.blit(t, t.get_rect(center=(SCREEN_W // 2, 180)))

        stats = [
            (f"Score    : {score}",    WHITE),
            (f"Distance : {distance}m", CYAN),
            (f"Coins    : {coins}",     GOLD),
        ]
        y = 255
        for text, col in stats:
            lbl = font.render(text, True, col)
            screen.blit(lbl, lbl.get_rect(center=(SCREEN_W // 2, y)))
            y += 40

        retry_btn.draw(screen)
        menu_btn.draw(screen)
        pygame.display.flip()


# ════════════════════════════════════════════════════════════════
#  HUD  (drawn every frame during gameplay)
# ════════════════════════════════════════════════════════════════

def draw_hud(surface, score, coins, distance, speed_level,
             powerup_name, powerup_timer, shield_active):
    font  = pygame.font.SysFont("Arial", 18, bold=True)
    small = pygame.font.SysFont("Arial", 13)
    GOLD_COL  = (255, 215, 0)
    HUD_ORANGE = (255, 160, 0)

    surface.blit(font.render(f"Score: {score}",    True, WHITE),    (10, 6))
    surface.blit(font.render(f"Coins: {coins}",    True, GOLD_COL), (SCREEN_W - 120, 6))
    surface.blit(small.render(f"Dist: {distance}m  Spd Lv {speed_level}", True, HUD_ORANGE), (10, 30))

    if powerup_name:
        col  = {"nitro": ORANGE, "shield": CYAN, "repair": GREEN}.get(powerup_name, WHITE)
        text = f"[{powerup_name.upper()}] {powerup_timer:.1f}s" if powerup_timer > 0 else f"[{powerup_name.upper()}]"
        surface.blit(small.render(text, True, col), (10, 48))

    if shield_active:
        lbl = small.render("🛡 SHIELD", True, CYAN)
        surface.blit(lbl, (SCREEN_W - 90, 30))


# ════════════════════════════════════════════════════════════════
#  INTERNAL BG HELPER
# ════════════════════════════════════════════════════════════════

def _draw_road_bg(surface):
    """Decorative static road strip on menu screens."""
    ROAD_LEFT, ROAD_RIGHT = 120, 280
    pygame.draw.rect(surface, (60, 60, 60), (ROAD_LEFT, 0, ROAD_RIGHT - ROAD_LEFT, SCREEN_H))
    pygame.draw.rect(surface, (200, 200, 200), (ROAD_LEFT - 3, 0, 3, SCREEN_H))
    pygame.draw.rect(surface, (200, 200, 200), (ROAD_RIGHT,    0, 3, SCREEN_H))

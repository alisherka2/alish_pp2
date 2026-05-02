# main.py — Screen manager: Main Menu, Leaderboard, Settings, then Game

import pygame
import sys

from config import *
from game import SnakeGame, load_settings, save_settings
import db as db_module

# ── Bootstrap DB ─────────────────────────────────────────────────────────────
db_module.init_db()


# ── Utility ───────────────────────────────────────────────────────────────────

def _draw_bg(surface):
    surface.fill(DARK_BG)
    # Subtle dot grid
    for x in range(0, SCREEN_W, 30):
        for y in range(0, SCREEN_H, 30):
            pygame.draw.circle(surface, (40, 40, 50), (x, y), 1)


def _draw_title(surface, font_big, font_small):
    title = font_big.render("🐍 SNAKE", True, ACCENT)
    sub   = font_small.render("TSIS4 Edition", True, SILVER)
    surface.blit(title, title.get_rect(center=(SCREEN_W // 2, 80)))
    surface.blit(sub,   sub.get_rect(center=(SCREEN_W // 2, 130)))


class Button:
    def __init__(self, rect, text, font, color=ACCENT, text_color=BLACK):
        self.rect       = pygame.Rect(rect)
        self.text       = text
        self.font       = font
        self.color      = color
        self.text_color = text_color

    def draw(self, surface, hover=False):
        col = tuple(min(255, c + 30) for c in self.color) if hover else self.color
        pygame.draw.rect(surface, col, self.rect, border_radius=8)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=8)
        txt = self.font.render(self.text, True, self.text_color)
        surface.blit(txt, txt.get_rect(center=self.rect.center))

    def is_hovered(self, pos):
        return self.rect.collidepoint(pos)

    def clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


# ── Main Menu ─────────────────────────────────────────────────────────────────

def screen_main_menu(screen, clock) -> tuple[str, str, int | None]:
    """
    Returns (action, username, player_id).
    action: "play" | "leaderboard" | "settings" | "quit"
    """
    font_big   = pygame.font.SysFont("arial", 52, bold=True)
    font_med   = pygame.font.SysFont("arial", 22, bold=True)
    font_small = pygame.font.SysFont("arial", 16)

    cx = SCREEN_W // 2
    buttons = {
        "play":        Button((cx - 110, 210, 220, 44), "▶  Play",        font_med),
        "leaderboard": Button((cx - 110, 270, 220, 44), "🏆  Leaderboard", font_med, GOLD, BLACK),
        "settings":    Button((cx - 110, 330, 220, 44), "⚙  Settings",    font_med, SILVER, BLACK),
        "quit":        Button((cx - 110, 390, 220, 44), "✕  Quit",        font_med, RED,  WHITE),
    }

    username = ""
    input_active = True
    error_msg    = ""

    while True:
        clock.tick(30)
        mouse_pos = pygame.mouse.get_pos()
        _draw_bg(screen)
        _draw_title(screen, font_big, font_small)

        # Username input box
        label = font_small.render("Enter username:", True, SILVER)
        screen.blit(label, (cx - 110, 165))
        box_rect = pygame.Rect(cx - 110, 183, 220, 26)
        pygame.draw.rect(screen, PANEL, box_rect, border_radius=5)
        border_col = ACCENT if input_active else SILVER
        pygame.draw.rect(screen, border_col, box_rect, 2, border_radius=5)
        uname_surf = font_small.render(username + ("|" if input_active else ""), True, WHITE)
        screen.blit(uname_surf, (box_rect.x + 6, box_rect.y + 5))

        if error_msg:
            err_surf = font_small.render(error_msg, True, RED)
            screen.blit(err_surf, err_surf.get_rect(center=(cx, 450)))

        for key, btn in buttons.items():
            btn.draw(screen, hover=btn.is_hovered(mouse_pos))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", "", None
            if event.type == pygame.KEYDOWN:
                if input_active:
                    if event.key == pygame.K_RETURN:
                        input_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        username = username[:-1]
                    else:
                        if len(username) < 20 and event.unicode.isprintable():
                            username += event.unicode
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if box_rect.collidepoint(event.pos):
                    input_active = True
                else:
                    input_active = False

            for key, btn in buttons.items():
                if btn.clicked(event):
                    if key == "quit":
                        return "quit", "", None
                    if key in ("play", "leaderboard", "settings"):
                        uname = username.strip()
                        if not uname:
                            error_msg = "Please enter a username first."
                            break
                        player_id = db_module.get_or_create_player(uname)
                        return key, uname, player_id


# ── Leaderboard ───────────────────────────────────────────────────────────────

def screen_leaderboard(screen, clock, current_username=""):
    font_big   = pygame.font.SysFont("arial", 36, bold=True)
    font_med   = pygame.font.SysFont("arial", 18, bold=True)
    font_small = pygame.font.SysFont("arial", 15)

    rows = db_module.get_top10()

    cx  = SCREEN_W // 2
    btn = Button((cx - 80, SCREEN_H - 60, 160, 40), "← Back", font_med)

    while True:
        clock.tick(30)
        mouse_pos = pygame.mouse.get_pos()
        _draw_bg(screen)

        title = font_big.render("🏆  Top 10 Leaderboard", True, GOLD)
        screen.blit(title, title.get_rect(center=(cx, 50)))

        # Table header
        cols_x = [40, 180, 330, 430, 530]
        headers = ["#", "Username", "Score", "Level", "Date"]
        for hdr, hx in zip(headers, cols_x):
            h = font_med.render(hdr, True, ACCENT)
            screen.blit(h, (hx, 90))
        pygame.draw.line(screen, SILVER, (30, 112), (SCREEN_W - 30, 112), 1)

        if not rows:
            no_data = font_small.render("No data — play a game first!", True, SILVER)
            screen.blit(no_data, no_data.get_rect(center=(cx, 200)))
        else:
            for i, row in enumerate(rows):
                y = 120 + i * 28
                rank_col = GOLD if i == 0 else (SILVER if i == 1 else WHITE)
                uname = row.get("username", "?")
                score = row.get("score", 0)
                level = row.get("level_reached", 1)
                date  = str(row.get("played_date", ""))[:10]

                # Highlight current user
                if uname == current_username:
                    pygame.draw.rect(screen, (30, 60, 30), (30, y - 2, SCREEN_W - 60, 24),
                                     border_radius=4)

                vals = [f"{i+1}.", uname, str(score), str(level), date]
                for val, hx in zip(vals, cols_x):
                    col = rank_col if hx == cols_x[0] else WHITE
                    s = font_small.render(val, True, col)
                    screen.blit(s, (hx, y))

        btn.draw(screen, hover=btn.is_hovered(mouse_pos))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_m):
                return "menu"
            if btn.clicked(event):
                return "menu"


# ── Settings ──────────────────────────────────────────────────────────────────

def screen_settings(screen, clock):
    font_big   = pygame.font.SysFont("arial", 32, bold=True)
    font_med   = pygame.font.SysFont("arial", 20, bold=True)
    font_small = pygame.font.SysFont("arial", 15)

    settings = load_settings()
    cx       = SCREEN_W // 2

    # Color presets
    color_presets = [
        ("Green",  [0, 210, 80]),
        ("Blue",   [30, 120, 255]),
        ("Red",    [220, 50, 50]),
        ("Yellow", [220, 200, 0]),
        ("Pink",   [255, 80, 180]),
        ("Cyan",   [0, 210, 210]),
    ]

    save_btn = Button((cx - 80, SCREEN_H - 65, 160, 42), "Save & Back", font_med, ACCENT, BLACK)

    while True:
        clock.tick(30)
        mouse_pos = pygame.mouse.get_pos()
        _draw_bg(screen)

        title = font_big.render("⚙  Settings", True, SILVER)
        screen.blit(title, title.get_rect(center=(cx, 50)))

        # Grid toggle
        grid_col = ACCENT if settings["grid_overlay"] else SILVER
        g_label  = font_med.render("Grid Overlay:", True, WHITE)
        g_val    = font_med.render("ON" if settings["grid_overlay"] else "OFF", True, grid_col)
        g_btn    = pygame.Rect(cx + 20, 110, 80, 32)
        screen.blit(g_label, (cx - 180, 114))
        pygame.draw.rect(screen, grid_col, g_btn, border_radius=6)
        screen.blit(g_val, g_val.get_rect(center=g_btn.center))

        # Sound toggle
        snd_col = ACCENT if settings["sound"] else SILVER
        s_label = font_med.render("Sound:", True, WHITE)
        s_val   = font_med.render("ON" if settings["sound"] else "OFF", True, snd_col)
        s_btn   = pygame.Rect(cx + 20, 160, 80, 32)
        screen.blit(s_label, (cx - 180, 164))
        pygame.draw.rect(screen, snd_col, s_btn, border_radius=6)
        screen.blit(s_val, s_val.get_rect(center=s_btn.center))

        # Snake color
        c_label = font_med.render("Snake Color:", True, WHITE)
        screen.blit(c_label, (cx - 180, 215))
        for idx, (name, rgb) in enumerate(color_presets):
            bx = cx - 165 + idx * 60
            by = 245
            r = pygame.Rect(bx, by, 52, 28)
            selected = tuple(settings["snake_color"]) == tuple(rgb)
            pygame.draw.rect(screen, rgb, r, border_radius=5)
            if selected:
                pygame.draw.rect(screen, WHITE, r, 3, border_radius=5)
            n_surf = font_small.render(name, True, WHITE)
            screen.blit(n_surf, n_surf.get_rect(center=(bx + 26, by + 38)))

        # Snake preview
        preview_col = tuple(settings["snake_color"])
        pygame.draw.rect(screen, preview_col,
                         (cx - 30, 310, 60, 20), border_radius=5)
        p_label = font_small.render("Preview", True, SILVER)
        screen.blit(p_label, p_label.get_rect(center=(cx, 342)))

        save_btn.draw(screen, hover=save_btn.is_hovered(mouse_pos))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_settings(settings)
                return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                save_settings(settings)
                return "menu"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if g_btn.collidepoint(event.pos):
                    settings["grid_overlay"] = not settings["grid_overlay"]
                elif s_btn.collidepoint(event.pos):
                    settings["sound"] = not settings["sound"]
                else:
                    for idx, (name, rgb) in enumerate(color_presets):
                        bx = cx - 165 + idx * 60
                        by = 245
                        r = pygame.Rect(bx, by, 52, 28)
                        if r.collidepoint(event.pos):
                            settings["snake_color"] = rgb
                if save_btn.clicked(event):
                    save_settings(settings)
                    return "menu"


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Snake — TSIS4")
    clock  = pygame.time.Clock()

    username  = ""
    player_id = None
    state     = "menu"

    while True:
        if state == "menu":
            action, username, player_id = screen_main_menu(screen, clock)
            state = action

        elif state == "play":
            game   = SnakeGame(username, player_id)
            result = game.run()
            state  = result    # "menu" or "quit"

        elif state == "leaderboard":
            result = screen_leaderboard(screen, clock, username)
            state  = result

        elif state == "settings":
            result = screen_settings(screen, clock)
            state  = result

        elif state == "quit":
            pygame.quit()
            sys.exit()

        else:
            state = "menu"


if __name__ == "__main__":
    main()

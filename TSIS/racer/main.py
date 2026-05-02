"""
main.py  –  TSIS 3  Racer
State machine:  menu → game → game_over → (retry | menu)
                menu → leaderboard → menu
                menu → settings    → menu
"""
import sys
import random
import pygame

from persistence import (
    load_settings, save_settings, load_leaderboard, add_score,
    CAR_COLORS, DIFFICULTY_SETTINGS,
)
from racer import COINS_PER_BOOST, SPEED_BOOST
from ui import (
    run_main_menu, run_settings, run_leaderboard, run_game_over, draw_hud,
)
from racer import (
    Road, PlayerCar, EnemyCar, Obstacle, Coin, PowerUp,
    SCREEN_W, SCREEN_H,
)

FPS = 60


# ════════════════════════════════════════════════════════════════
#  GAME SESSION
# ════════════════════════════════════════════════════════════════

def run_game(screen, clock, settings):
    """
    One full game session.
    Returns (score, distance, coins) when the player dies.
    """
    diff    = DIFFICULTY_SETTINGS[settings.get("difficulty", "normal")]
    car_col = CAR_COLORS[settings.get("car_color", "blue")]

    road   = Road()
    player = PlayerCar(color=car_col)

    enemies:   list[EnemyCar]  = []
    coins:     list[Coin]      = []
    obstacles: list[Obstacle]  = []
    powerups:  list[PowerUp]   = []

    score      = 0
    coin_count = 0
    base_speed = diff["base_speed"]
    distance   = 0        # metres (1 frame ≈ 0.05 m at base speed)
    game_over  = False

    # ── timers (frames) ──
    enemy_timer    = 0
    enemy_interval = diff["enemy_interval"]
    coin_timer     = 0
    coin_interval  = random.randint(100, 180)
    obs_timer      = 0
    obs_interval   = diff["obstacle_interval"]
    pu_timer       = 0
    pu_interval    = random.randint(300, 500)   # power-up every ~5–8 s

    # ── power-up state ──
    active_pu      = None   # name of active power-up
    nitro_timer    = 0.0    # seconds remaining for nitro
    shield_active  = False

    # ── speed ──
    speed_level  = 1
    current_speed = base_speed

    while True:
        dt = clock.tick(FPS) / 1000.0   # seconds

        # ── EVENTS ────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return score, distance, coin_count

        # ── UPDATE ────────────────────────────────────────────
        if not game_over:
            keys = pygame.key.get_pressed()

            # nitro active?
            nitro_on = (active_pu == "nitro" and nitro_timer > 0)
            if nitro_on:
                nitro_timer = max(0.0, nitro_timer - dt)
                if nitro_timer <= 0:
                    active_pu = None

            player.move(keys, nitro_active=nitro_on)
            road.update()

            # ── speed scaling ──
            coin_boosts   = coin_count // COINS_PER_BOOST
            current_speed = base_speed + coin_boosts * SPEED_BOOST
            speed_level   = coin_boosts + 1
            road.speed    = 5 + coin_boosts

            # distance
            distance += int(current_speed * 0.05)

            # ── spawn enemies ──
            enemy_timer += 1
            if enemy_timer >= enemy_interval:
                enemies.append(EnemyCar(current_speed, player_x=int(player.x)))
                enemy_timer    = 0
                enemy_interval = max(35, diff["enemy_interval"] - coin_boosts * 3)

            # ── spawn coins ──
            coin_timer += 1
            if coin_timer >= coin_interval:
                coins.append(Coin(current_speed))
                coin_timer    = 0
                coin_interval = random.randint(80, 180)

            # ── spawn obstacles ──
            obs_timer += 1
            if obs_timer >= obs_interval:
                obstacles.append(Obstacle(current_speed))
                obs_timer    = 0
                obs_interval = max(60, diff["obstacle_interval"] - coin_boosts * 5)

            # ── spawn power-ups ──
            pu_timer += 1
            if pu_timer >= pu_interval:
                powerups.append(PowerUp(current_speed))
                pu_timer    = 0
                pu_interval = random.randint(280, 480)

            # ── update enemies ──
            for en in enemies[:]:
                en.update()
                if en.off_screen():
                    enemies.remove(en)
                    score += 1
                elif en.rect().colliderect(player.rect()):
                    if shield_active:
                        shield_active = False
                        active_pu     = None
                        enemies.remove(en)
                    else:
                        game_over = True

            # ── update coins ──
            for co in coins[:]:
                co.update()
                if co.off_screen():
                    coins.remove(co)
                elif co.rect().colliderect(player.rect()):
                    coins.remove(co)
                    coin_count += co.value
                    score      += co.value

            # ── update obstacles ──
            oil_slow = False
            for ob in obstacles[:]:
                ob.update()
                if ob.off_screen():
                    obstacles.remove(ob)
                elif ob.rect().colliderect(player.rect()):
                    if ob.kind == "barrier":
                        if shield_active:
                            shield_active = False
                            active_pu     = None
                            obstacles.remove(ob)
                        else:
                            game_over = True
                    elif ob.kind == "oil":
                        oil_slow = True   # slow enemies while player is on oil
                    elif ob.kind == "nitro":
                        # road nitro strip: free speed boost
                        road.speed = min(road.speed + 3, 18)
                        obstacles.remove(ob)

            # ── update power-ups ──
            for pu in powerups[:]:
                pu.update(dt)
                if pu.off_screen():
                    powerups.remove(pu)
                elif pu.rect().colliderect(player.rect()):
                    powerups.remove(pu)
                    _apply_powerup(pu, active_pu,
                                   # closures for mutating local state
                                   _state := {"active_pu": active_pu,
                                              "nitro_timer": nitro_timer,
                                              "shield_active": shield_active})
                    active_pu     = _state["active_pu"]
                    nitro_timer   = _state["nitro_timer"]
                    shield_active = _state["shield_active"]

        # ── DRAW ──────────────────────────────────────────────
        road.draw(screen)

        for ob in obstacles:  ob.draw(screen)
        for en in enemies:    en.draw(screen)
        for co in coins:      co.draw(screen)
        for pu in powerups:   pu.draw(screen)

        player.draw(screen, shield_active=shield_active)

        draw_hud(screen, score, coin_count, distance, speed_level,
                 active_pu, nitro_timer if active_pu == "nitro" else 0,
                 shield_active)

        # coin legend
        _draw_coin_legend(screen)

        if game_over:
            pygame.display.flip()
            return score, distance, coin_count

        pygame.display.flip()


def _apply_powerup(pu, current_active, state):
    """Mutate state dict in-place (avoids nonlocal complexity)."""
    if pu.name == "nitro":
        state["active_pu"]    = "nitro"
        state["nitro_timer"]  = pu.dur
    elif pu.name == "shield":
        state["active_pu"]      = "shield"
        state["shield_active"]  = True
    elif pu.name == "repair":
        # Repair: instant – clears active negative effect; no persistent state
        state["active_pu"] = None


def _draw_coin_legend(surface):
    from racer import COIN_TYPES
    small = pygame.font.SysFont("Arial", 13)
    x, y  = 10, SCREEN_H - 22
    for tier in COIN_TYPES:
        pygame.draw.circle(surface, tier["colour"], (x+5, y+6), 6)
        lbl = small.render(f"+{tier['value']}", True, tier["colour"])
        surface.blit(lbl, (x+14, y))
        x += 46


# ════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════════

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Racer – TSIS 3")
    clock = pygame.time.Clock()

    settings = load_settings()

    state = "menu"
    while True:
        if state == "menu":
            state = run_main_menu(screen, clock, settings)
            save_settings(settings)

        elif state == "play":
            score, distance, coins = run_game(screen, clock, settings)
            username = settings.get("username", "Player") or "Player"
            board    = add_score(username, score, distance, coins)
            state    = run_game_over(screen, clock, score, distance, coins)

        elif state == "retry":
            score, distance, coins = run_game(screen, clock, settings)
            username = settings.get("username", "Player") or "Player"
            board    = add_score(username, score, distance, coins)
            state    = run_game_over(screen, clock, score, distance, coins)

        elif state == "leaderboard":
            board = load_leaderboard()
            run_leaderboard(screen, clock, board)
            state = "menu"

        elif state == "settings":
            settings = run_settings(screen, clock, settings)
            save_settings(settings)
            state = "menu"

        elif state == "quit":
            save_settings(settings)
            pygame.quit()
            sys.exit()


if __name__ == "__main__":
    main()

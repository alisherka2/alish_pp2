"""
persistence.py  –  TSIS 3
Save / load settings.json and leaderboard.json
"""
import json
import os

SETTINGS_FILE    = "settings.json"
LEADERBOARD_FILE = "leaderboard.json"

DEFAULT_SETTINGS = {
    "sound":       False,
    "car_color":   "blue",    # "blue" | "red" | "green" | "yellow"
    "difficulty":  "normal",  # "easy" | "normal" | "hard"
    "username":    "",
}

CAR_COLORS = {
    "blue":   (30,  90,  210),
    "red":    (210, 30,   30),
    "green":  (30,  160,  60),
    "yellow": (220, 200,   0),
}

DIFFICULTY_SETTINGS = {
    "easy":   {"base_speed": 3,  "enemy_interval": 110, "obstacle_interval": 200},
    "normal": {"base_speed": 4,  "enemy_interval": 80,  "obstacle_interval": 150},
    "hard":   {"base_speed": 6,  "enemy_interval": 55,  "obstacle_interval": 100},
}


def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            # fill any missing keys with defaults
            for k, v in DEFAULT_SETTINGS.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


def load_leaderboard() -> list:
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_leaderboard(board: list):
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(board, f, indent=2)


def add_score(username: str, score: int, distance: int, coins: int):
    """Insert entry, keep top 10 sorted by score descending."""
    board = load_leaderboard()
    board.append({"name": username, "score": score,
                  "distance": distance, "coins": coins})
    board.sort(key=lambda e: e["score"], reverse=True)
    board = board[:10]
    save_leaderboard(board)
    return board

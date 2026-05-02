"""
tools.py  –  PhoneBook TSIS 2
All drawing helpers, flood-fill, and shape dispatchers.
"""
import pygame
import math
from collections import deque

# ── tool IDs ────────────────────────────────────────────────
TOOL_PENCIL    = "pencil"
TOOL_LINE      = "line"
TOOL_RECTANGLE = "rectangle"
TOOL_SQUARE    = "square"
TOOL_CIRCLE    = "circle"
TOOL_ERASER    = "eraser"
TOOL_RTRIANGLE = "right_tri"
TOOL_ETRIANGLE = "eq_tri"
TOOL_RHOMBUS   = "rhombus"
TOOL_FILL      = "fill"
TOOL_TEXT      = "text"

# ── brush sizes ──────────────────────────────────────────────
BRUSH_SIZES = [2, 5, 10]   # small / medium / large

CANVAS_COLOR = (255, 255, 255)


# ════════════════════════════════════════════════════════════
#  GEOMETRY HELPERS  (same as Practice 11, unchanged)
# ════════════════════════════════════════════════════════════

def right_triangle_points(sx, sy, ex, ey):
    return [(sx, sy), (ex, sy), (sx, ey)]


def equilateral_triangle_points(sx, sy, ex, ey):
    base   = abs(ex - sx)
    height = int(math.sqrt(3) / 2 * base)
    apex_x = (sx + ex) // 2
    apex_y = ey - height
    return [(sx, ey), (ex, ey), (apex_x, apex_y)]


def rhombus_points(sx, sy, ex, ey):
    mx = (sx + ex) // 2
    my = (sy + ey) // 2
    return [(mx, sy), (ex, my), (mx, ey), (sx, my)]


def square_rect(sx, sy, ex, ey):
    side = min(abs(ex - sx), abs(ey - sy))
    rx = sx if ex >= sx else sx - side
    ry = sy if ey >= sy else sy - side
    return pygame.Rect(rx, ry, side, side)


# ════════════════════════════════════════════════════════════
#  SHAPE DISPATCHER  (brush_size now passed in)
# ════════════════════════════════════════════════════════════

def draw_shape(surface, tool, color, sx, sy, ex, ey, brush_size=2):
    """
    Render one shape onto *surface*.
    brush_size controls the outline width for all closed shapes,
    and the line thickness for the line tool.
    """
    lw = brush_size

    if tool == TOOL_LINE:
        pygame.draw.line(surface, color, (sx, sy), (ex, ey), lw)

    elif tool == TOOL_RECTANGLE:
        rect = pygame.Rect(min(sx,ex), min(sy,ey), abs(ex-sx), abs(ey-sy))
        pygame.draw.rect(surface, color, rect, lw)

    elif tool == TOOL_SQUARE:
        rect = square_rect(sx, sy, ex, ey)
        pygame.draw.rect(surface, color, rect, lw)

    elif tool == TOOL_CIRCLE:
        cx_ = (sx + ex) // 2
        cy_ = (sy + ey) // 2
        radius = max(abs(ex-sx), abs(ey-sy)) // 2
        if radius > 0:
            pygame.draw.circle(surface, color, (cx_, cy_), radius, lw)

    elif tool == TOOL_RTRIANGLE:
        pts = right_triangle_points(sx, sy, ex, ey)
        pygame.draw.polygon(surface, color, pts, lw)

    elif tool == TOOL_ETRIANGLE:
        pts = equilateral_triangle_points(sx, sy, ex, ey)
        pygame.draw.polygon(surface, color, pts, lw)

    elif tool == TOOL_RHOMBUS:
        pts = rhombus_points(sx, sy, ex, ey)
        pygame.draw.polygon(surface, color, pts, lw)

    # PENCIL, ERASER, FILL, TEXT handled inline in paint.py


# ════════════════════════════════════════════════════════════
#  FLOOD FILL  (BFS, pixel-level)
# ════════════════════════════════════════════════════════════

def flood_fill(surface, x, y, fill_color):
    """
    BFS flood-fill starting at (x, y) on *surface*.
    Replaces the target colour with fill_color.
    Exact colour match (no tolerance).
    """
    w, h = surface.get_size()

    # Clamp start point inside surface bounds
    x = max(0, min(x, w - 1))
    y = max(0, min(y, h - 1))

    target_color = surface.get_at((x, y))[:3]   # ignore alpha
    fill_rgb     = fill_color[:3]

    if target_color == fill_rgb:
        return   # already that colour – nothing to do

    queue   = deque()
    queue.append((x, y))
    visited = set()
    visited.add((x, y))

    # Lock for faster pixel access
    surface.lock()
    while queue:
        cx, cy = queue.popleft()
        if surface.get_at((cx, cy))[:3] != target_color:
            continue
        surface.set_at((cx, cy), fill_rgb)
        for nx, ny in ((cx-1,cy),(cx+1,cy),(cx,cy-1),(cx,cy+1)):
            if 0 <= nx < w and 0 <= ny < h and (nx,ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny))
    surface.unlock()


# ════════════════════════════════════════════════════════════
#  TEXT STATE  (used by paint.py)
# ════════════════════════════════════════════════════════════

class TextState:
    """Holds the in-progress text placement state."""

    def __init__(self):
        self.active   = False
        self.pos      = (0, 0)   # canvas-local position
        self.buffer   = ""       # characters typed so far

    def start(self, x, y):
        self.active = True
        self.pos    = (x, y)
        self.buffer = ""

    def cancel(self):
        self.active = False
        self.buffer = ""

    def add_char(self, ch):
        self.buffer += ch

    def backspace(self):
        self.buffer = self.buffer[:-1]

    def commit(self, surface, color, font):
        """Render text permanently onto *surface*."""
        if self.buffer.strip():
            label = font.render(self.buffer, True, color)
            surface.blit(label, self.pos)
        self.cancel()

    def draw_preview(self, surface, color, font):
        """Show typed text + blinking cursor on *surface* (call every frame)."""
        if not self.active:
            return
        preview = self.buffer + "|"
        label   = font.render(preview, True, color)
        surface.blit(label, self.pos)

import pygame
import sys
import math

# ══════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════

WINDOW_WIDTH  = 960
WINDOW_HEIGHT = 680
TOOLBAR_H     = 65          # height of the top toolbar strip
CANVAS_TOP    = TOOLBAR_H   # canvas starts right below the toolbar

# Ten colours the user can pick from
PALETTE = [
    (0,   0,   0),    # black
    (255, 255, 255),  # white
    (255,   0,   0),  # red
    (0,   220,   0),  # green
    (0,     0, 255),  # blue
    (255, 255,   0),  # yellow
    (255, 128,   0),  # orange
    (160,   0, 255),  # purple
    (0,   220, 255),  # cyan
    (255,   0, 200),  # magenta
]

SWATCH_SIZE   = 28   # pixel size of each colour swatch
SWATCH_MARGIN = 5    # gap between swatches

# Tool identifier strings
TOOL_PENCIL    = "pencil"
TOOL_RECTANGLE = "rectangle"
TOOL_SQUARE    = "square"
TOOL_CIRCLE    = "circle"
TOOL_ERASER    = "eraser"
TOOL_RTRIANGLE = "right_tri"    # right triangle
TOOL_ETRIANGLE = "eq_tri"       # equilateral triangle
TOOL_RHOMBUS   = "rhombus"

CANVAS_COLOR   = (255, 255, 255)  # white drawing surface
TOOLBAR_COLOR  = (28,  28,  40)   # dark toolbar background
BORDER_COLOR   = (70,  70, 100)   # separator line colour


# ══════════════════════════════════════════════
#  GEOMETRY HELPERS
# ══════════════════════════════════════════════

def right_triangle_points(sx, sy, ex, ey):
    """
    Return the three vertices of a right triangle.
    The right angle sits at (sx, sy).
    The two legs go horizontally to (ex, sy) and vertically to (sx, ey).
    """
    return [(sx, sy), (ex, sy), (sx, ey)]


def equilateral_triangle_points(sx, sy, ex, ey):
    """
    Return the three vertices of an equilateral triangle.
    The base runs from (sx, ey) to (ex, ey).
    The apex is centred above (or below) the base at the correct height
    so that all three sides are equal.

    Height of equilateral triangle = (sqrt(3) / 2) * base
    """
    base   = abs(ex - sx)
    height = int(math.sqrt(3) / 2 * base)

    # Ensure apex is above the base (move upward in screen coords)
    apex_x = (sx + ex) // 2
    apex_y = ey - height   # subtract because y grows downward

    return [(sx, ey), (ex, ey), (apex_x, apex_y)]


def rhombus_points(sx, sy, ex, ey):
    """
    Return four vertices of a rhombus (diamond shape).
    The bounding box is defined by the drag from (sx,sy) to (ex,ey).
    Vertices are at the midpoints of each side of that bounding box.
    """
    mx = (sx + ex) // 2   # horizontal midpoint
    my = (sy + ey) // 2   # vertical midpoint
    return [
        (mx, sy),   # top
        (ex, my),   # right
        (mx, ey),   # bottom
        (sx, my),   # left
    ]


def square_rect(sx, sy, ex, ey):
    """
    Return a pygame.Rect for a square.
    The side length equals the smaller of the horizontal/vertical drag distance,
    and the square grows toward the drag direction.
    """
    side = min(abs(ex - sx), abs(ey - sy))
    # preserve sign of drag direction
    rx = sx if ex >= sx else sx - side
    ry = sy if ey >= sy else sy - side
    return pygame.Rect(rx, ry, side, side)


# ══════════════════════════════════════════════
#  UI HELPERS
# ══════════════════════════════════════════════

def draw_button(surface, font, text, rect, active=False):
    """Draw a rounded toolbar button. Highlighted when active=True."""
    fill_color   = (80, 160, 255)  if active else (55, 55, 78)
    border_color = (200, 225, 255) if active else (100, 100, 130)

    pygame.draw.rect(surface, fill_color,   rect, border_radius=6)
    pygame.draw.rect(surface, border_color, rect, 2, border_radius=6)

    label = font.render(text, True, (240, 240, 240))
    lx = rect.x + (rect.width  - label.get_width())  // 2
    ly = rect.y + (rect.height - label.get_height()) // 2
    surface.blit(label, (lx, ly))


# ══════════════════════════════════════════════
#  MAIN FUNCTION
# ══════════════════════════════════════════════

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Practice 11 – Paint (Extended)")
    font  = pygame.font.SysFont(None, 19)
    clock = pygame.time.Clock()

    # ── white canvas surface (persistent drawing area) ──
    canvas = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT - CANVAS_TOP))
    canvas.fill(CANVAS_COLOR)

    # ── application state ──
    current_tool  = TOOL_PENCIL
    current_color = PALETTE[0]      # default: black
    brush_size    = 4               # pencil radius in pixels
    eraser_size   = 18              # eraser radius in pixels

    drawing      = False            # True while mouse button is held
    start_pos    = None             # canvas-space position where drag began
    preview_surf = None             # temporary surface for shape preview

    # ── tool definitions: (id, label, keyboard shortcut char) ──
    tools = [
        (TOOL_PENCIL,    "Pencil",   "P"),
        (TOOL_RECTANGLE, "Rect",     "R"),
        (TOOL_SQUARE,    "Square",   "Q"),
        (TOOL_CIRCLE,    "Circle",   "C"),
        (TOOL_ERASER,    "Eraser",   "E"),
        (TOOL_RTRIANGLE, "R-Tri",    "T"),
        (TOOL_ETRIANGLE, "Eq-Tri",   "Y"),
        (TOOL_RHOMBUS,   "Rhombus",  "U"),
    ]

    # ── build button rects dynamically based on tool count ──
    btn_w, btn_h = 76, 38
    btn_y = (TOOLBAR_H - btn_h) // 2
    tool_rects = []
    for i in range(len(tools)):
        r = pygame.Rect(8 + i * (btn_w + 4), btn_y, btn_w, btn_h)
        tool_rects.append(r)

    # ── build colour swatch rects, placed after the last button ──
    palette_rects = []
    px_start = 8 + len(tools) * (btn_w + 4) + 16   # left edge of first swatch
    for i in range(len(PALETTE)):
        r = pygame.Rect(
            px_start + i * (SWATCH_SIZE + SWATCH_MARGIN),
            (TOOLBAR_H - SWATCH_SIZE) // 2,
            SWATCH_SIZE,
            SWATCH_SIZE,
        )
        palette_rects.append(r)

    # ── keyboard shortcut lookup: char → tool id ──
    key_map = {tool[2]: tool[0] for tool in tools}

    # ══════════════════════════════════════════
    #  MAIN LOOP
    # ══════════════════════════════════════════
    running = True
    while running:

        # ── process events ──
        for event in pygame.event.get():

            # window close button
            if event.type == pygame.QUIT:
                running = False
                break

            # ── keyboard shortcuts ──
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    # map pressed key to a tool shortcut if one exists
                    char = pygame.key.name(event.key).upper()
                    if char in key_map:
                        current_tool = key_map[char]

            # ── mouse button pressed ──
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # check toolbar UI first
                clicked_ui = False

                for i, r in enumerate(tool_rects):
                    if r.collidepoint(mx, my):
                        current_tool = tools[i][0]
                        clicked_ui   = True
                        break

                for i, r in enumerate(palette_rects):
                    if r.collidepoint(mx, my):
                        current_color = PALETTE[i]
                        clicked_ui    = True
                        break

                # start drawing if the click was on the canvas
                if not clicked_ui and my >= CANVAS_TOP:
                    drawing   = True
                    # convert to canvas-local coordinates
                    start_pos = (mx, my - CANVAS_TOP)

            # ── mouse dragged ──
            elif event.type == pygame.MOUSEMOTION:
                if drawing:
                    mx, my = event.pos
                    cy = my - CANVAS_TOP          # canvas-local y

                    if current_tool == TOOL_PENCIL:
                        # paint a filled circle at cursor position
                        pygame.draw.circle(canvas, current_color,
                                           (mx, cy), brush_size)

                    elif current_tool == TOOL_ERASER:
                        # erase by drawing a white circle
                        pygame.draw.circle(canvas, CANVAS_COLOR,
                                           (mx, cy), eraser_size)

                    else:
                        # all other tools show a ghost preview while dragging
                        preview_surf = canvas.copy()
                        sx, sy = start_pos
                        _draw_shape(preview_surf, current_tool,
                                    current_color, sx, sy, mx, cy)

            # ── mouse button released – commit the shape ──
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if drawing:
                    mx, my = event.pos
                    cy = my - CANVAS_TOP
                    sx, sy = start_pos if start_pos else (mx, cy)

                    # write final shape directly onto the canvas
                    _draw_shape(canvas, current_tool,
                                current_color, sx, sy, mx, cy)

                    # reset drag state
                    drawing      = False
                    start_pos    = None
                    preview_surf = None

        # ══════════════════════════════════════
        #  RENDER
        # ══════════════════════════════════════

        # dark toolbar background
        screen.fill(TOOLBAR_COLOR)

        # canvas (use preview during drag, committed canvas otherwise)
        blit_surface = preview_surf if preview_surf else canvas
        screen.blit(blit_surface, (0, CANVAS_TOP))

        # horizontal line separating toolbar from canvas
        pygame.draw.line(screen, BORDER_COLOR,
                         (0, TOOLBAR_H), (WINDOW_WIDTH, TOOLBAR_H), 2)

        # tool buttons
        for i, (tid, label, shortcut) in enumerate(tools):
            draw_button(screen, font,
                        f"{label} [{shortcut}]",
                        tool_rects[i],
                        active=(current_tool == tid))

        # colour swatches
        for i, r in enumerate(palette_rects):
            pygame.draw.rect(screen, PALETTE[i], r, border_radius=4)
            # white border on the currently selected colour
            sel = (255, 255, 255) if current_color == PALETTE[i] else (60, 60, 70)
            pygame.draw.rect(screen, sel, r, 2, border_radius=4)

        # small status text at the very bottom of the window
        status_text = (
            f"Tool: {current_tool}   |   ESC = quit"
        )
        status = font.render(status_text, True, (160, 160, 160))
        screen.blit(status, (10, WINDOW_HEIGHT - 20))

        pygame.display.flip()
        clock.tick(60)   # cap at 60 FPS

    pygame.quit()
    sys.exit()


# ══════════════════════════════════════════════
#  SHAPE DISPATCHER
# ══════════════════════════════════════════════

def _draw_shape(surface, tool, color, sx, sy, ex, ey):
    """
    Draw the selected shape onto 'surface' using outline (width=2).

    Parameters
    ----------
    surface : pygame.Surface  – target (canvas or preview copy)
    tool    : str             – one of the TOOL_* constants
    color   : tuple           – RGB colour
    sx, sy  : int             – start corner in canvas coordinates
    ex, ey  : int             – end corner (current mouse position)
    """
    line_w = 2   # outline thickness for all shapes

    if tool == TOOL_RECTANGLE:
        # Axis-aligned rectangle defined by two opposite corners
        rect = pygame.Rect(
            min(sx, ex), min(sy, ey),
            abs(ex - sx), abs(ey - sy)
        )
        pygame.draw.rect(surface, color, rect, line_w)

    elif tool == TOOL_SQUARE:
        # Square: same as rectangle but sides are equal (min of w/h)
        rect = square_rect(sx, sy, ex, ey)
        pygame.draw.rect(surface, color, rect, line_w)

    elif tool == TOOL_CIRCLE:
        # Circle inscribed in the bounding box of the drag
        cx_ = (sx + ex) // 2
        cy_ = (sy + ey) // 2
        radius = max(abs(ex - sx), abs(ey - sy)) // 2
        if radius > 0:
            pygame.draw.circle(surface, color, (cx_, cy_), radius, line_w)

    elif tool == TOOL_RTRIANGLE:
        # Right triangle – right angle at the drag start point
        pts = right_triangle_points(sx, sy, ex, ey)
        pygame.draw.polygon(surface, color, pts, line_w)

    elif tool == TOOL_ETRIANGLE:
        # Equilateral triangle – base along bottom of drag box
        pts = equilateral_triangle_points(sx, sy, ex, ey)
        pygame.draw.polygon(surface, color, pts, line_w)

    elif tool == TOOL_RHOMBUS:
        # Rhombus (diamond) – vertices at midpoints of drag bounding box
        pts = rhombus_points(sx, sy, ex, ey)
        pygame.draw.polygon(surface, color, pts, line_w)

    # TOOL_PENCIL and TOOL_ERASER are handled inline in the motion event
    # (they paint pixel-by-pixel) so they are not needed here.


# ══════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════
if __name__ == "__main__":
    main()
